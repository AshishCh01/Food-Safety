import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, Float, ForeignKey, Index, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database import Base
from app.utils.enums import ComplaintPriority, TriageStatus


class ComplaintTriage(Base):
    """AI-generated complaint triage analysis, stored separately from the
    citizen-submitted complaint record (see docs/AI_AGENTS_ARCHITECTURE.md
    section 4). Purely advisory - nothing here ever overwrites `Complaint`
    fields or drives a status transition automatically.

    A complaint may accumulate more than one row (an officer can re-run
    triage), so callers should read the latest row by `created_at` rather
    than assuming a single record per complaint.
    """

    __tablename__ = "complaint_triage_results"
    __table_args__ = (Index("ix_complaint_triage_complaint_created", "complaint_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True
    )
    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[TriageStatus] = mapped_column(
        SAEnum(TriageStatus, name="triage_status", values_callable=lambda e: [i.value for i in e]),
        nullable=False,
    )
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)

    # Category suggestion. `suggested_category_id` is only ever set to a real,
    # active row in `complaint_categories` (the authoritative taxonomy) - a
    # Gemini label that doesn't map cleanly is recorded in
    # `suggested_category_raw` instead/as well and flagged uncertain, never
    # invented as a new category.
    suggested_category_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("complaint_categories.id", ondelete="SET NULL"), nullable=True
    )
    suggested_category_raw: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category_match_uncertain: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Advisory only - reuses the same enum/table as Complaint.priority but is
    # never written back onto the complaint itself.
    suggested_priority: Mapped[ComplaintPriority | None] = mapped_column(
        SAEnum(ComplaintPriority, name="complaint_priority", values_callable=lambda e: [i.value for i in e]),
        nullable=True,
    )

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    entities: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    missing_information: Mapped[list | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_uncertain: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    complaint: Mapped["Complaint"] = relationship()
    suggested_category: Mapped["ComplaintCategory | None"] = relationship()
    requested_by: Mapped["User"] = relationship()
