import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.config import get_settings
from app.core.database import Base
from app.core.vector_types import EmbeddingVector

_EMBEDDING_DIM = get_settings().gemini_embedding_dimensions


class RagDocumentChunk(Base):
    """One retrievable chunk of a `RagDocument`, carrying enough metadata to be
    filtered and cited independently of the parent document (see
    docs/RAG_ARCHITECTURE.md sections 5-6). `chunk_metadata` denormalizes the
    parent document's filterable attributes (document_type/business_type/
    jurisdiction/version/effective_date) at ingestion time so retrieval can
    filter without a join; `document_id` remains the source of truth for
    provenance/citations.
    """

    __tablename__ = "rag_document_chunks"
    __table_args__ = (Index("ix_rag_chunks_document_chunk_index", "document_id", "chunk_index"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("rag_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    heading_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    chunk_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    embedding: Mapped[list[float]] = mapped_column(EmbeddingVector(_EMBEDDING_DIM), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    document: Mapped["RagDocument"] = relationship(back_populates="chunks")
