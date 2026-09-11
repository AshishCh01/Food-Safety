import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database import Base


class ComplaintClarification(Base):
    __tablename__ = 'complaint_clarifications'
    __table_args__ = (Index('ix_complaint_clarifications_complaint_id', 'complaint_id'),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey('complaints.id', ondelete='CASCADE'), nullable=False, index=True
    )
    # The officer's message is stored in ComplaintStatusHistory.reason for the
    # INSUFFICIENT_EVIDENCE transition; we keep a FK here so the citizen can retrieve
    # it via a single join without scanning status_history.
    request_history_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey('complaint_status_history.id', ondelete='SET NULL'), nullable=True
    )
    requested_by_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey('staff_profiles.id', ondelete='RESTRICT'), nullable=False
    )
    response_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    responded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    complaint: Mapped['Complaint'] = relationship(back_populates='clarifications')
    request_history: Mapped['ComplaintStatusHistory | None'] = relationship()
    requested_by: Mapped['StaffProfile'] = relationship()
    responded_by: Mapped['User | None'] = relationship()