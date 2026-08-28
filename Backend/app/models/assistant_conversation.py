import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database import Base


class AssistantConversation(Base):
    """A conversation between one inspector and the Inspector Assistant (see
    docs/AI_AGENTS_ARCHITECTURE.md section 7). Always scoped to exactly one
    inspector; optionally scoped to one inspection (and its complaint, kept
    denormalized here for convenient filtering) for follow-up questions "within
    an inspection/complaint context". A conversation with no inspection is a
    general regulatory Q&A session.
    """

    __tablename__ = "assistant_conversations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    inspector_staff_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("staff_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    inspection_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("inspections.id", ondelete="SET NULL"), nullable=True, index=True
    )
    complaint_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("complaints.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    inspector: Mapped["StaffProfile"] = relationship()
    inspection: Mapped["Inspection | None"] = relationship()
    complaint: Mapped["Complaint | None"] = relationship()
    messages: Mapped[list["AssistantMessage"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="AssistantMessage.created_at",
    )
