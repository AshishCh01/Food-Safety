from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.agents.inspector_assistant.agent import ask_stream
from app.core.database import get_db
from app.core.rate_limit import voice_turn_rate_limiter
from app.schemas.agent import VoiceTurnRequest
from app.services import assistant_service

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/turn", dependencies=[Depends(voice_turn_rate_limiter)])
def voice_turn(payload: VoiceTurnRequest, db: Session = Depends(get_db)) -> StreamingResponse:
    """Streams the Inspector Assistant's answer as Server-Sent Events, one
    `data: <text delta>\\n\\n` frame per chunk, so the voice worker's TTS can
    start speaking the first sentence before the rest of the answer is
    generated. session_token resolves the inspector/conversation exactly as
    before - see app.services.assistant_service.resolve_voice_session."""
    staff, conversation = assistant_service.resolve_voice_session(db, payload.session_token)

    def event_stream():
        for delta in ask_stream(db, staff, conversation, payload.transcript):
            yield f"data: {delta}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")