import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database import Base
from app.utils.enums import RagDocumentStatus, RagDocumentType


class RagDocument(Base):
    """An official food-safety source document (law, regulation, inspection
    guideline, department SOP, ...) uploaded to the RAG knowledge base (see
    docs/RAG_ARCHITECTURE.md). Kept entirely separate from transactional
    complaint/inspection data - nothing here is ever linked to a specific
    complaint or business.

    A document starts `pending`, moves to `ingested` once
    `app.rag.ingestion.ingest_document` has chunked and embedded it, or
    `failed` if that could not complete. `is_active` lets an admin deactivate
    a source (see docs/RAG_ARCHITECTURE.md section 12) without deleting it;
    retrieval only ever considers `status=ingested, is_active=True` documents.
    """

    __tablename__ = "rag_documents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source_organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    document_type: Mapped[RagDocumentType] = mapped_column(
        SAEnum(RagDocumentType, name="rag_document_type", values_callable=lambda e: [i.value for i in e]),
        nullable=False,
        index=True,
    )
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(100), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    business_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    jurisdiction: Mapped[str] = mapped_column(String(100), nullable=False, default="India")

    status: Mapped[RagDocumentStatus] = mapped_column(
        SAEnum(RagDocumentStatus, name="rag_document_status", values_callable=lambda e: [i.value for i in e]),
        nullable=False,
        default=RagDocumentStatus.PENDING,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    superseded_by_document_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("rag_documents.id", ondelete="SET NULL"), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    uploaded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    uploaded_by: Mapped["User"] = relationship(foreign_keys=[uploaded_by_user_id])
    chunks: Mapped[list["RagDocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", passive_deletes=True
    )
