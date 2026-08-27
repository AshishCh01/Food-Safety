import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database import Base
from app.utils.enums import ComplaintStatus


class ComplaintStatusHistory(Base):
    __tablename__ = "complaint_status_history"
    __table_args__ = (Index("ix_complaint_status_history_complaint_created", "complaint_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True
    )
    old_status: Mapped[ComplaintStatus | None] = mapped_column(
        SAEnum(ComplaintStatus, name="complaint_status", values_callable=lambda e: [i.value for i in e]),
        nullable=True,
    )
    new_status: Mapped[ComplaintStatus] = mapped_column(
        SAEnum(ComplaintStatus, name="complaint_status", values_callable=lambda e: [i.value for i in e]),
        nullable=False,
    )
    changed_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    complaint: Mapped["Complaint"] = relationship(back_populates="status_history")
    changed_by: Mapped["User"] = relationship()
