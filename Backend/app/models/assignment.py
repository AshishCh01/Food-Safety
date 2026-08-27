import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database import Base
from app.utils.enums import AssignmentStatus


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_to_staff_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("staff_profiles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    assigned_by_staff_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("staff_profiles.id", ondelete="RESTRICT"), nullable=False
    )
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[AssignmentStatus] = mapped_column(
        SAEnum(AssignmentStatus, name="assignment_status", values_callable=lambda e: [i.value for i in e]),
        nullable=False,
        default=AssignmentStatus.ASSIGNED,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    complaint: Mapped["Complaint"] = relationship()
    assigned_to: Mapped["StaffProfile"] = relationship(foreign_keys=[assigned_to_staff_id])
    assigned_by: Mapped["StaffProfile"] = relationship(foreign_keys=[assigned_by_staff_id])
