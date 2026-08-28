import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Index, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database import Base
from app.utils.enums import AssistantMessageRole


class AssistantMessage(Base):
    """One turn in an `AssistantConversation`. `citations` and
    `application_data_used` are small, code-attached summaries (never raw
    tool/RAG payloads) - see docs/AI_AGENTS_ARCHITECTURE.md section 13
    (no unrestricted agent memory; durable facts stay in the application
    database) and section 16 (log metadata, not secrets). A failed assistant
    turn is persisted with `error_code`/`error_message` set rather than a
    fabricated answer.
    """

    __tablename__ = "assistant_messages"
    __table_args__ = (Index("ix_assistant_messages_conversation_created", "conversation_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("assistant_conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[AssistantMessageRole] = mapped_column(
        SAEnum(AssistantMessageRole, name="assistant_message_role", values_callable=lambda e: [i.value for i in e]),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    citations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    application_data_used: Mapped[list | None] = mapped_column(JSON, nullable=True)
    is_uncertain: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    uncertainty_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    conversation: Mapped["AssistantConversation"] = relationship(back_populates="messages")
