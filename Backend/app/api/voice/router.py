"""Voice-turn endpoint for the Inspector Assistant, called by an external
voice AI platform (e.g. Dograh) rather than by the authenticated React
frontend. Deliberately NOT mounted under app.api.inspector.router (which
requires the inspector's own login access token via require_inspector) -
the voice platform never holds that token. Authorization here comes
entirely from the short-lived, single-conversation-scoped token minted by
POST /inspector/assistant/conversations/{id}/voice-session, resolved in
app.services.assistant_service.resolve_voice_session.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limit import voice_turn_rate_limiter
from app.schemas.agent import VoiceTurnRequest, VoiceTurnResponse
from app.services import assistant_service

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post(
    "/turn",
    response_model=VoiceTurnResponse,
    dependencies=[Depends(voice_turn_rate_limiter)],
)
def voice_turn(
    payload: VoiceTurnRequest,
    db: Session = Depends(get_db),
) -> VoiceTurnResponse:
    """One turn of a voice conversation: `session_token` resolves the
    inspector/conversation (never trusted from any other field in the
    payload), `transcript` is fed into the same Inspector Assistant
    pipeline a typed question goes through - the RAG/agent logic itself
    (app.agents.inspector_assistant.agent.ask) is completely unaware this
    came from a voice platform rather than the app."""
    staff, conversation = assistant_service.resolve_voice_session(db, payload.session_token)
    message = assistant_service.ask(db, staff, conversation, payload.transcript)
    return VoiceTurnResponse(
        answer=message.content,
        is_uncertain=message.is_uncertain,
        uncertainty_reason=message.uncertainty_reason,
    )