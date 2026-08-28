import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, Float, ForeignKey, Index, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database import Base
from app.utils.enums import InvestigationStatus


class InvestigationBrief(Base):
    """AI-generated investigation brief for a District Officer (Phase 9, see
    docs/AI_AGENTS_ARCHITECTURE.md section 6), stored separately from the
    citizen-submitted complaint and the inspector's inspection record. Purely
    advisory - nothing here overwrites `Complaint`/`Inspection` data, drives a
    status transition, imposes a penalty, or represents a final regulatory
    decision; those remain with the district officer.

    `relevant_evidence` and `business_history` are populated directly from
    controlled tool results (never model-generated prose) so those facts can
    never be fabricated - only `case_summary`, `complaint_patterns`,
    `risk_indicators`, `suggested_actions`, and `regulatory_guidance` are
    model-generated, and every `regulatory_guidance` entry carries a citation
    resolved against an actually-retrieved RAG chunk (see
    app/agents/investigation/agent.py) - an item whose citation cannot be
    resolved is dropped rather than shown uncited.

    A complaint may accumulate more than one row (an officer can re-run the
    investigation), so callers should read the latest row by `created_at`
    rather than assuming a single record per complaint.
    """

    __tablename__ = "investigation_briefs"
    __table_args__ = (Index("ix_investigation_briefs_complaint_created", "complaint_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True
    )
    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[InvestigationStatus] = mapped_column(
        SAEnum(InvestigationStatus, name="investigation_status", values_callable=lambda e: [i.value for i in e]),
        nullable=False,
    )
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)

    case_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Deterministic, code-populated from controlled tools - never model prose.
    relevant_evidence: Mapped[list | None] = mapped_column(JSON, nullable=True)
    business_history: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Model-generated analytical layer, always grounded in the tool-fetched
    # data above and the retrieved RAG chunks - never invented facts.
    complaint_patterns: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # list[{"guidance": str, "citation": {...RagCitation}}] - every entry's
    # citation is resolved against a retrieved chunk; entries whose citation
    # could not be resolved are dropped before persistence.
    regulatory_guidance: Mapped[list | None] = mapped_column(JSON, nullable=True)
    risk_indicators: Mapped[list | None] = mapped_column(JSON, nullable=True)
    missing_information: Mapped[list | None] = mapped_column(JSON, nullable=True)
    suggested_actions: Mapped[list | None] = mapped_column(JSON, nullable=True)

    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_uncertain: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    uncertainty_reasons: Mapped[list | None] = mapped_column(JSON, nullable=True)

    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    complaint: Mapped["Complaint"] = relationship()
    requested_by: Mapped["User"] = relationship()
