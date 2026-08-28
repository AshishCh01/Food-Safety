import uuid

from sqlalchemy.orm import Session

from app.agents.inspector_assistant import agent as inspector_assistant_agent
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
from app.utils.exceptions import AssistantConversationNotFoundError


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
