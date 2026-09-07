import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.agents.inspector_assistant import agent as inspector_assistant_agent
from app.core.config import get_settings
from app.core.security import TokenType, create_voice_session_token, decode_token
from app.models.assistant_conversation import AssistantConversation
from app.models.assistant_message import AssistantMessage
from app.models.staff_profile import StaffProfile
from app.repositories import assistant_repository
from app.schemas.agent import (
    AssistantApplicationDataUsage,
    AssistantConversationRead,
    AssistantConversationSummary,
    AssistantMessageRead,
)
from app.schemas.rag import RagCitation
from app.services import inspection_service
from app.utils.exceptions import AssistantConversationNotFoundError, InvalidTokenError, PermissionDeniedError
import json

from livekit import api as livekit_api


def create_conversation(db: Session, staff: StaffProfile, inspection_id: uuid.UUID | None) -> AssistantConversation:
    """Creates a conversation scoped to `staff`. When `inspection_id` is
    given, ownership is verified via the same scoped lookup the rest of the
    inspector API uses (inspection_service.get_inspection_for_inspector) -
    never trusted from the request body alone."""
    complaint_id = None
    if inspection_id is not None:
        inspection = inspection_service.get_inspection_for_inspector(db, staff.id, inspection_id)
        complaint_id = inspection.complaint_id

    conversation = AssistantConversation(
        inspector_staff_id=staff.id,
        inspection_id=inspection_id,
        complaint_id=complaint_id,
    )
    return assistant_repository.create_conversation(db, conversation)


def get_conversation_for_inspector(
    db: Session, staff: StaffProfile, conversation_id: uuid.UUID
) -> AssistantConversation:
    conversation = assistant_repository.get_by_id(db, conversation_id)
    if conversation is None or conversation.inspector_staff_id != staff.id:
        raise AssistantConversationNotFoundError()
    return conversation

def create_voice_session_token_for_conversation(
    staff: StaffProfile, conversation: AssistantConversation
) -> tuple[str, datetime]:
    """Issues a short-lived token scoped to this one conversation, to hand
    to an external voice platform instead of the inspector's own login
    token. `conversation` must already be resolved via
    get_conversation_for_inspector by the caller - same ownership-check
    pattern used everywhere else in this service."""
    settings = get_settings()
    expires_delta = timedelta(minutes=settings.voice_session_token_expire_minutes)
    token = create_voice_session_token(conversation.id, staff.id, expires_delta)
    expires_at = datetime.now(timezone.utc) + expires_delta
    return token, expires_at

def create_livekit_session_for_conversation(staff: StaffProfile, conversation: AssistantConversation) -> "LiveKitSessionRead":
    """Mints a LiveKit room-join token for the inspector's browser, with the
    internal voice_session_token embedded as agent-dispatch metadata rather
    than returned to the client - the LiveKit worker (a separate Python
    process, not this backend) receives it via JobContext.job.metadata once
    dispatched, and uses it to call POST /api/v1/voice/turn exactly like an
    external voice platform would (see app/api/voice/router.py)."""
    from app.schemas.agent import LiveKitSessionRead  # local import avoids a circular import at module load time

    settings = get_settings()
    voice_session_token, _ = create_voice_session_token_for_conversation(staff, conversation)

    room_name = f"inspector-assistant-{conversation.id}"
    dispatch_metadata = json.dumps(
        {"voice_session_token": voice_session_token, "conversation_id": str(conversation.id)}
    )
    room_config = livekit_api.RoomConfiguration(
        agents=[livekit_api.RoomAgentDispatch(agent_name=settings.livekit_agent_name, metadata=dispatch_metadata)],
    )

    ttl = timedelta(minutes=settings.livekit_room_token_expire_minutes)
    token = (
        livekit_api.AccessToken(settings.livekit_api_key.get_secret_value(), settings.livekit_api_secret.get_secret_value())
        .with_identity(f"inspector-{staff.id}")
        .with_name(staff.user.full_name)
        .with_grants(livekit_api.VideoGrants(room_join=True, room=room_name, can_publish=True, can_subscribe=True))
        .with_room_config(room_config)
        .with_ttl(ttl)
    )

    return LiveKitSessionRead(
        livekit_url=settings.livekit_url,
        room_name=room_name,
        access_token=token.to_jwt(),
        expires_at=datetime.now(timezone.utc) + ttl,
    )


def resolve_voice_session(db: Session, session_token: str) -> tuple[StaffProfile, AssistantConversation]:
    """Resolves a voice-session token back to the staff/conversation it was
    issued for. This is the only authorization check on the voice-turn
    endpoint (app/api/voice/router.py) - nothing here may trust a
    conversation_id or staff_id from anywhere other than this signed token."""
    payload = decode_token(session_token, TokenType.VOICE_SESSION)
    try:
        conversation_id = uuid.UUID(payload["sub"])
        staff_id = uuid.UUID(payload["staff_id"])
    except (KeyError, ValueError) as exc:
        raise InvalidTokenError() from exc

    conversation = assistant_repository.get_by_id(db, conversation_id)
    if conversation is None or conversation.inspector_staff_id != staff_id:
        raise AssistantConversationNotFoundError()

    staff = conversation.inspector
    if staff is None or not staff.is_active:
        raise PermissionDeniedError("Staff profile is not active.")

    return staff, conversation


def list_conversations_for_inspector(
    db: Session,
    staff: StaffProfile,
    *,
    inspection_id: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[AssistantConversation], int]:
    return assistant_repository.list_for_inspector(
        db, staff.id, inspection_id=inspection_id, page=page, page_size=page_size
    )


def ask(db: Session, staff: StaffProfile, conversation: AssistantConversation, question: str) -> AssistantMessage:
    return inspector_assistant_agent.ask(db, staff, conversation, question)


def ask_stream(db: Session, staff: StaffProfile, conversation: AssistantConversation, question: str):
    return inspector_assistant_agent.ask_stream(db, staff, conversation, question)


def to_message_read(message: AssistantMessage) -> AssistantMessageRead:
    return AssistantMessageRead(
        id=message.id,
        role=message.role,
        content=message.content,
        citations=[RagCitation(**entry) for entry in (message.citations or [])],
        application_data_used=[
            AssistantApplicationDataUsage(**entry) for entry in (message.application_data_used or [])
        ],
        is_uncertain=message.is_uncertain,
        uncertainty_reason=message.uncertainty_reason,
        error_code=message.error_code,
        error_message=message.error_message,
        created_at=message.created_at,
    )


def to_conversation_read(conversation: AssistantConversation) -> AssistantConversationRead:
    return AssistantConversationRead(
        id=conversation.id,
        inspection_id=conversation.inspection_id,
        complaint_id=conversation.complaint_id,
        title=conversation.title,
        messages=[to_message_read(message) for message in conversation.messages],
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def to_conversation_summary(conversation: AssistantConversation) -> AssistantConversationSummary:
    return AssistantConversationSummary(
        id=conversation.id,
        inspection_id=conversation.inspection_id,
        complaint_id=conversation.complaint_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )
