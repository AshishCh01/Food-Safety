import json
import uuid
import asyncio
import logging
import re
import websockets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import get_settings
from app.core.dependencies import get_ws_staff_profile
from app.services import assistant_service

logger = logging.getLogger("inspector-voice-ws")

ws_router = APIRouter()

class VoiceSessionManager:
    def __init__(self):
        self.active_sessions: dict[uuid.UUID, uuid.UUID] = {}

    def start_session(self, conversation_id: uuid.UUID, voice_session_id: uuid.UUID):
        self.active_sessions[conversation_id] = voice_session_id

    def is_active(self, conversation_id: uuid.UUID, voice_session_id: uuid.UUID) -> bool:
        return self.active_sessions.get(conversation_id) == voice_session_id

    def stop_session(self, conversation_id: uuid.UUID, voice_session_id: uuid.UUID):
        if self.is_active(conversation_id, voice_session_id):
            del self.active_sessions[conversation_id]

manager = VoiceSessionManager()


def remove_citations_for_speech(text: str) -> str:
    """Removes [R1], [A2] style citations from text before sending to TTS."""
    return re.sub(r'\[(R|A)\d+\]', '', text)


async def run_stt_loop(websocket: WebSocket, conversation_id: uuid.UUID, voice_session_id: uuid.UUID, deepgram_ws):
    """Reads STT results from Deepgram and forwards them to the client."""
    try:
        async for message in deepgram_ws:
            if not manager.is_active(conversation_id, voice_session_id):
                break
                
            data = json.loads(message)
            if data.get("type") == "Results":
                is_final = data.get("is_final", False)
                alts = data.get("channel", {}).get("alternatives", [])
                if alts:
                    transcript = alts[0].get("transcript", "")
                    if transcript:
                        await websocket.send_json({
                            "type": "transcript_final" if is_final else "transcript_partial",
                            "text": transcript
                        })
    except Exception as e:
        logger.error(f"Deepgram loop error: {e}")


async def generate_and_speak(
    websocket: WebSocket,
    conversation_id: uuid.UUID,
    voice_session_id: uuid.UUID,
    staff_id: uuid.UUID,
    question: str,
    cartesia_ws
):
    """Runs the LLM via ask_stream, sends chunks to Cartesia, and forwards audio to the client."""
    from starlette.concurrency import iterate_in_threadpool
    from app.core.database import SessionLocal
    from app.repositories.staff_repository import get_by_id as get_staff_by_id
    
    context_id = str(uuid.uuid4())
    await websocket.send_json({"type": "assistant_start"})
    
    sentence_buffer = ""

    def _sync_ask_stream():
        db = SessionLocal()
        try:
            staff = get_staff_by_id(db, staff_id)
            conversation = assistant_service.get_conversation_for_inspector(db, staff, conversation_id)
            yield from assistant_service.ask_stream(db, staff, conversation, question, is_voice=True)
        finally:
            db.close()

    try:
        async_gen = iterate_in_threadpool(_sync_ask_stream())
        
        full_response = ""
        
        async for item in async_gen:
            if not manager.is_active(conversation_id, voice_session_id):
                break
                
            if isinstance(item, dict):
                # Final metadata, send citations back to client
                item["type"] = "assistant_end"
                await websocket.send_json(item)
                
                logger.info(f"[{voice_session_id}] AI responded: {full_response}")
                
                # Close the TTS context
                if cartesia_ws:
                    await cartesia_ws.send(json.dumps({
                        "context_id": context_id,
                        "model_id": "sonic-latest",
                        "transcript": "",
                        "voice": {"mode": "id", "id": "3b554273-4299-48b9-9aaf-eefd438e3941"},
                        "output_format": {
                            "container": "raw",
                            "encoding": "pcm_f32le",
                            "sample_rate": 16000
                        },
                        "continue": False
                    }))
                break
            else:
                # Text delta
                # Clean out citations for speech
                clean_text = remove_citations_for_speech(item)
                sentence_buffer += clean_text
                full_response += item
                
                # Send the raw (uncleaned) text delta to the client so UI gets citations
                await websocket.send_json({"type": "assistant_text", "text": item})
                
                # Send to Cartesia if we have enough words or a punctuation mark
                if cartesia_ws and (len(sentence_buffer) > 20 or any(p in sentence_buffer for p in '.?!,\n')):
                    if sentence_buffer.strip():
                        req = {
                            "context_id": context_id,
                            "model_id": "sonic-latest",
                            "transcript": sentence_buffer,
                            "voice": {"mode": "id", "id": "3b554273-4299-48b9-9aaf-eefd438e3941"},
                            "output_format": {
                                "container": "raw",
                                "encoding": "pcm_f32le",
                                "sample_rate": 16000
                            },
                            "continue": True
                        }
                        await cartesia_ws.send(json.dumps(req))
                    sentence_buffer = ""

    except Exception as e:
        logger.error(f"LLM Error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": "I couldn't process that question. Please try again."})
        except:
            pass


async def run_tts_loop(websocket: WebSocket, conversation_id: uuid.UUID, voice_session_id: uuid.UUID, cartesia_ws):
    """Reads audio results from Cartesia and forwards them to the client."""
    import base64
    try:
        async for message in cartesia_ws:
            if not manager.is_active(conversation_id, voice_session_id):
                break
            data = json.loads(message)
            if data.get("type") == "chunk" and "data" in data:
                # cartesia returns base64 string, we decode and send binary
                audio_bytes = base64.b64decode(data["data"])
                await websocket.send_bytes(audio_bytes)
            elif data.get("type") == "error":
                logger.error(f"Cartesia error: {data}")
    except Exception as e:
        logger.error(f"Cartesia loop error: {e}")


@ws_router.websocket("/ws/{conversation_id}")
async def voice_websocket(
    websocket: WebSocket,
    conversation_id: uuid.UUID,
    token: str,
    db: Session = Depends(get_db),
):
    # Manually authenticate since Depends() with Query doesn't always play nice in WebSockets
    try:
        staff = get_ws_staff_profile(token=token, db=db)
        conversation = assistant_service.get_conversation_for_inspector(db, staff, conversation_id)
    except Exception as e:
        logger.error(f"WebSocket auth failed: {e}")
        await websocket.close(code=1008, reason="Unauthorized")
        return

    await websocket.accept()

    voice_session_id = uuid.uuid4()
    manager.start_session(conversation_id, voice_session_id)
    logger.info(f"Started voice session {voice_session_id} for conversation {conversation_id}")
    
    settings = get_settings()
    
    deepgram_url = "wss://api.deepgram.com/v1/listen?model=nova-3-general&encoding=linear16&sample_rate=16000&channels=1&endpointing=300"
    cartesia_url = "wss://api.cartesia.ai/tts/websocket?cartesia_version=2026-08-14"

    deepgram_ws = None
    cartesia_ws = None
    
    tasks = []

    try:
        # Connect to providers
        deepgram_api_key = settings.deepgram_api_key.get_secret_value()
        cartesia_api_key = settings.cartesia_api_key.get_secret_value()
        
        deepgram_ws = await websockets.connect(deepgram_url, additional_headers={"Authorization": f"Token {deepgram_api_key}"})
        cartesia_ws = await websockets.connect(cartesia_url, additional_headers={"X-API-Key": cartesia_api_key, "Cartesia-Version": "2026-08-14"})
        
        tasks.append(asyncio.create_task(run_stt_loop(websocket, conversation_id, voice_session_id, deepgram_ws)))
        tasks.append(asyncio.create_task(run_tts_loop(websocket, conversation_id, voice_session_id, cartesia_ws)))
        
        await websocket.send_json({
            "type": "ready",
            "voice_session_id": str(voice_session_id)
        })

        # Send a quick initial greeting so the assistant speaks first
        greeting_text = "Hi, I'm your Inspector Assistant. How can I help you?"
        greeting_context = str(uuid.uuid4())
        
        logger.info(f"[{voice_session_id}] AI greeted: {greeting_text}")
        
        await websocket.send_json({"type": "assistant_start"})
        await websocket.send_json({"type": "assistant_text", "text": greeting_text})
        
        await cartesia_ws.send(json.dumps({
            "context_id": greeting_context,
            "model_id": "sonic-latest",
            "transcript": greeting_text,
            "voice": {"mode": "id", "id": "3b554273-4299-48b9-9aaf-eefd438e3941"},
            "output_format": {
                "container": "raw",
                "encoding": "pcm_f32le",
                "sample_rate": 16000
            },
            "continue": False
        }))
        
        await websocket.send_json({"type": "assistant_end"})

        current_agent_task = None
        while manager.is_active(conversation_id, voice_session_id):
            message = await websocket.receive()
            if "text" in message:
                data = json.loads(message["text"])
                msg_type = data.get("type")
                if msg_type == "start":
                    pass
                elif msg_type == "closed":
                    manager.stop_session(conversation_id, voice_session_id)
                    break
                elif msg_type == "stop_agent":
                    if current_agent_task and not current_agent_task.done():
                        current_agent_task.cancel()
                        current_agent_task = None
                elif msg_type == "invoke_agent":
                    # Deepgram endpointing triggered final transcript, client sends invoke
                    transcript = data.get("text", "").strip()
                    if transcript:
                        logger.info(f"[{voice_session_id}] Inspector asked: {transcript}")
                        if current_agent_task and not current_agent_task.done():
                            current_agent_task.cancel()
                        current_agent_task = asyncio.create_task(generate_and_speak(
                            websocket, conversation_id, voice_session_id, staff.id, transcript, cartesia_ws
                        ))
            elif "bytes" in message:
                audio_data = message["bytes"]
                if deepgram_ws:
                    await deepgram_ws.send(audio_data)

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from {voice_session_id}")
    except Exception as e:
        logger.error(f"Error in voice session {voice_session_id}: {e}")
        try:
            await websocket.send_json({"type": "error", "message": "Voice connection error."})
        except:
            pass
    finally:
        manager.stop_session(conversation_id, voice_session_id)
        if deepgram_ws:
            await deepgram_ws.close()
        if cartesia_ws:
            await cartesia_ws.close()
        for task in tasks:
            task.cancel()
        logger.info(f"Closed voice session {voice_session_id}")
