"""LiveKit Agent worker for the Inspector Assistant voice channel.

Standalone process, run separately from the FastAPI app (its own pm2
process). Connects to LiveKit Cloud, gets dispatched into whichever room a
browser joins via app.services.assistant_service.create_livekit_session_for_conversation,
and pipes the inspector's speech through STT -> the existing Inspector
Assistant RAG pipeline (over HTTP, POST /api/v1/voice/turn on the FastAPI
backend) -> TTS. Holds no direct database access and no RAG logic of its
own - this is purely the voice I/O layer (docs/AI_AGENTS_ARCHITECTURE.md).

The llm_node() override below fully replaces LLM generation with a call to
our own backend, following LiveKit's documented "Replacing LLM output"
pattern (https://docs.livekit.io/recipes/replacing_llm_output/) - the
AgentSession still needs an `llm=` instance passed to it to construct
correctly, but it is never actually invoked since llm_node never calls
self.session.llm.chat(...).

on_user_turn_completed() no longer speaks its filler unconditionally - after
the backend's answer stage went Groq-primary, most turns finish in 2-8s, and
a filler on every single turn (including "thank you") felt sluggish and
robotic rather than helpful. Instead it schedules the filler on a delay
(FILLER_DELAY_SECONDS) and llm_node cancels that pending task the moment the
real answer is ready - so the filler only ever plays when the backend is
genuinely slow enough to need it.
"""

import asyncio
import json
import logging
import os

import httpx
from dotenv import load_dotenv
from livekit.agents import Agent, AgentServer, AgentSession, JobContext, JobProcess, cli, inference
from livekit.plugins import silero

load_dotenv(".env.local")

logger = logging.getLogger("inspector-voice-worker")
logger.setLevel(logging.INFO)

BACKEND_BASE_URL = os.environ["BACKEND_BASE_URL"]  # e.g. http://localhost:8000, or your EC2 backend URL
VOICE_TURN_PATH = "/api/v1/voice/turn"
HTTP_TIMEOUT_SECONDS = 45.0
AGENT_NAME = os.environ.get("LIVEKIT_AGENT_NAME", "inspector-voice-assistant")
FILLER_DELAY_SECONDS = 2.5

server = AgentServer()


def prewarm(proc: JobProcess) -> None:
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


class InspectorAssistant(Agent):
    def __init__(self, session_token: str) -> None:
        super().__init__(
            instructions=(
                "You are the Inspector Assistant, speaking with a food-safety "
                "inspector in the field. Keep replies short, plain, and speakable - "
                "no markdown, no bullet points, no asterisks."
            )
        )
        self._session_token = session_token
        self._filler_task: asyncio.Task | None = None

    async def on_enter(self) -> None:
        await self.session.say("Hi, I'm the Inspector Assistant. What do you need help with?")

    async def on_user_turn_completed(self, chat_ctx, new_message) -> None:
        # Don't speak immediately - only if the backend hasn't answered
        # within FILLER_DELAY_SECONDS. llm_node cancels this task as soon as
        # it has the real answer, so a fast turn never hears the filler.
        async def _delayed_filler() -> None:
            await asyncio.sleep(FILLER_DELAY_SECONDS)
            self.session.say("Let me check on that.")

        if self._filler_task and not self._filler_task.done():
            self._filler_task.cancel()
        self._filler_task = asyncio.create_task(_delayed_filler())

    async def llm_node(self, chat_ctx, tools, model_settings=None):
        async def process_stream():
            transcript = ""
            for item in reversed(chat_ctx.items):
                if getattr(item, "role", None) == "user":
                    transcript = item.text_content or ""
                    break

            if not transcript:
                if self._filler_task and not self._filler_task.done():
                    self._filler_task.cancel()
                yield "Sorry, I didn't catch that - could you say it again?"
                return

            try:
                async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
                    response = await client.post(
                        f"{BACKEND_BASE_URL}{VOICE_TURN_PATH}",
                        json={"transcript": transcript, "session_token": self._session_token},
                    )
                    response.raise_for_status()
                    result = response.json()
            except httpx.HTTPError:
                logger.exception("voice-turn request failed")
                if self._filler_task and not self._filler_task.done():
                    self._filler_task.cancel()
                yield "Sorry, I couldn't reach the assistant just now - please try again."
                return

            if self._filler_task and not self._filler_task.done():
                self._filler_task.cancel()

            answer = result.get("answer", "")
            if result.get("is_uncertain") and result.get("uncertainty_reason"):
                answer = f"{answer} {result['uncertainty_reason']}"
            yield answer

        return process_stream()


@server.rtc_session(agent_name=AGENT_NAME)
async def entrypoint(ctx: JobContext) -> None:
    metadata = json.loads(ctx.job.metadata or "{}")
    session_token = metadata.get("voice_session_token")
    if not session_token:
        logger.error("Voice job dispatched with no voice_session_token in metadata - refusing to start")
        return

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),  # never actually called - see class docstring
        tts=inference.TTS(model="cartesia/sonic-3", voice="3b554273-4299-48b9-9aaf-eefd438e3941"),
        vad=ctx.proc.userdata["vad"],
        turn_detection=inference.TurnDetector(),
    )

    agent = InspectorAssistant(session_token)
    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)