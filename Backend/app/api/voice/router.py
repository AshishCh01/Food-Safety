import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limit import voice_turn_rate_limiter
from app.schemas.agent import VoiceTurnRequest
from app.services import assistant_service

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/turn", dependencies=[Depends(voice_turn_rate_limiter)])
def voice_turn(payload: VoiceTurnRequest, db: Session = Depends(get_db)) -> StreamingResponse:
    """Streams the Inspector Assistant's answer as Server-Sent Events, one
    `data: <text delta>\\n\\n` frame per text chunk, so the voice worker's TTS
    can start speaking the first sentence before the rest of the answer is
    generated. session_token resolves the inspector/conversation exactly as
    before - see app.services.assistant_service.resolve_voice_session."""
    staff, conversation = assistant_service.resolve_voice_session(db, payload.session_token)

    def event_stream():
        for item in assistant_service.ask_stream(db, staff, conversation, payload.transcript):
            if isinstance(item, dict):
                # Final metadata payload - send as JSON for clients that want it,
                # then signal end-of-stream with [DONE]
                yield f"data: {json.dumps(item)}\n\n"
                yield "data: [DONE]\n\n"
                return
            else:
                # Plain text token delta - send as-is for the TTS pipeline
                yield f"data: {item}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")