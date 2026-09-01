import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database import Base
from app.utils.enums import InspectionStatus


class Inspection(Base):
    __tablename__ = "inspections"
    # Composite index for the "my active cases" query pattern (inspector_id
    # equality + optional status equality) used by
    # inspection_repository.list_by_inspector - see docs/DATABASE_SCHEMA.md
    # section 22 and docs/PROJECT_AUDIT_REPORT.md finding 1.8.
    __table_args__ = (Index("ix_inspections_inspector_status", "inspector_id", "inspection_status"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    inspector_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("staff_profiles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    inspection_status: Mapped[InspectionStatus] = mapped_column(
        SAEnum(InspectionStatus, name="inspection_status", values_callable=lambda e: [i.value for i in e]),
        nullable=False,
        default=InspectionStatus.SCHEDULED,
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_recommended: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_storage_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    complaint: Mapped["Complaint"] = relationship()
    inspector: Mapped["StaffProfile"] = relationship()
    findings: Mapped[list["InspectionFinding"]] = relationship(
        back_populates="inspection", cascade="all, delete-orphan", order_by="InspectionFinding.created_at"
    )
