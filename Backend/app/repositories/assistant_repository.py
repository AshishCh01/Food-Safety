import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.assistant_conversation import AssistantConversation
from app.models.assistant_message import AssistantMessage

_EAGER_OPTIONS = (joinedload(AssistantConversation.messages),)


def create_conversation(db: Session, conversation: AssistantConversation) -> AssistantConversation:
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_by_id(db: Session, conversation_id: uuid.UUID) -> AssistantConversation | None:
    stmt = select(AssistantConversation).where(AssistantConversation.id == conversation_id).options(*_EAGER_OPTIONS)
    return db.execute(stmt).unique().scalar_one_or_none()


def list_for_inspector(
    db: Session,
    inspector_staff_id: uuid.UUID,
    *,
    inspection_id: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[AssistantConversation], int]:
    stmt = select(AssistantConversation).where(AssistantConversation.inspector_staff_id == inspector_staff_id)
    if inspection_id is not None:
        stmt = stmt.where(AssistantConversation.inspection_id == inspection_id)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    stmt = (
        stmt.order_by(AssistantConversation.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    items = list(db.execute(stmt).scalars().all())
    return items, total


def create_message(db: Session, message: AssistantMessage) -> AssistantMessage:
    db.add(message)
    db.flush()
    return message


def list_messages(db: Session, conversation_id: uuid.UUID) -> list[AssistantMessage]:
    stmt = (
        select(AssistantMessage)
        .where(AssistantMessage.conversation_id == conversation_id)
        .order_by(AssistantMessage.created_at)
    )
    return list(db.execute(stmt).scalars().all())
