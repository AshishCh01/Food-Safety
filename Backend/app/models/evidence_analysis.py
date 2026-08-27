import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, Float, ForeignKey, Index, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database import Base
from app.utils.enums import EvidenceAnalysisStatus


class EvidenceAnalysis(Base):
    """AI-generated evidence analysis (OCR/vision), stored separately from the
    citizen/inspector-uploaded `Evidence` record (see
    docs/AI_AGENTS_ARCHITECTURE.md section 5). Purely advisory - nothing here
    ever overwrites the original evidence file or `Evidence` row, and it never
    marks a product as legally expired/non-compliant; `possible_expired` is a
    heuristic flag for officer/inspector review only.

    An evidence item may accumulate more than one row (re-analysis can be
    explicitly requested), so callers should read the latest row by
    `created_at` rather than assuming a single record per evidence item.
    """

    __tablename__ = "evidence_analysis_results"
    __table_args__ = (Index("ix_evidence_analysis_evidence_created", "evidence_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    evidence_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("evidence.id", ondelete="CASCADE"), nullable=False, index=True
    )
    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[EvidenceAnalysisStatus] = mapped_column(
        SAEnum(EvidenceAnalysisStatus, name="evidence_analysis_status", values_callable=lambda e: [i.value for i in e]),
        nullable=False,
    )
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)

    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    batch_lot_number: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Raw as extracted from the image/label - never parsed into a Date column,
    # since packaging dates are frequently partial or ambiguous (e.g. "MFG
    # 03/2026"). `possible_expired` is the deterministic, code-side
    # interpretation of `expiry_date_text`, kept separate from the raw value.
    manufacturing_date_text: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expiry_date_text: Mapped[str | None] = mapped_column(String(100), nullable=True)
    possible_expired: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    packaging_observations: Mapped[str | None] = mapped_column(Text, nullable=True)
    hygiene_observations: Mapped[str | None] = mapped_column(Text, nullable=True)
    foreign_object_observations: Mapped[str | None] = mapped_column(Text, nullable=True)

    uncertainty_notes: Mapped[list | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_uncertain: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    evidence: Mapped["Evidence"] = relationship()
    requested_by: Mapped["User"] = relationship()
