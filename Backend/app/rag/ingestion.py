"""Ingestion orchestration: parse -> chunk -> embed -> store
(docs/RAG_ARCHITECTURE.md section 4). Runs synchronously from the admin ingest
endpoint, matching the existing synchronous-agent-call pattern used by
Complaint Triage / Evidence Analysis (an explicit POST triggers the run; no
background queue exists in this phase).
"""

import time

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.rag_document import RagDocument
from app.models.rag_document_chunk import RagDocumentChunk
from app.rag import chunking, parsing
from app.repositories import rag_chunk_repository, rag_document_repository
from app.services import ai_service
from app.utils.enums import RagDocumentStatus
from app.utils.exceptions import AppError, GeminiRateLimitedError, GeminiUnavailableError, RagIngestionError

_MAX_EMBED_ATTEMPTS = 2
_RETRY_BACKOFF_SECONDS = 1.0
_RETRYABLE_EXCEPTIONS = (GeminiRateLimitedError, GeminiUnavailableError)


def _embed_with_retry(text: str) -> list[float]:
    for attempt in range(1, _MAX_EMBED_ATTEMPTS + 1):
        try:
            return ai_service.embed_text(text)
        except _RETRYABLE_EXCEPTIONS:
            if attempt < _MAX_EMBED_ATTEMPTS:
                time.sleep(_RETRY_BACKOFF_SECONDS * attempt)
                continue
            raise
    raise AssertionError("unreachable")  # pragma: no cover


def ingest_document(db: Session, document: RagDocument, file_bytes: bytes) -> RagDocument:
    """Parses, chunks, and embeds `document`'s file. Any existing chunks for
    this document are replaced (safe to re-run on `pending`/`failed`/
    `ingested` documents). Leaves no partial chunks behind on failure - the
    document is marked `failed` with `error_message` set instead."""
    settings = get_settings()
    rag_chunk_repository.delete_by_document(db, document.id)
    db.flush()

    try:
        pages = parsing.load_document(file_bytes, document.file_type)
        pieces = chunking.chunk_pages(pages)
        if not pieces:
            raise RagIngestionError("No extractable text was found in this document.")

        chunk_rows = [
            RagDocumentChunk(
                document_id=document.id,
                chunk_index=piece.chunk_index,
                content=piece.content,
                page_number=piece.page_number,
                section_title=piece.section_title,
                heading_path=piece.section_title,
                chunk_metadata={
                    "document_type": document.document_type.value,
                    "business_type": document.business_type,
                    "jurisdiction": document.jurisdiction,
                    "version": document.version,
                },
                embedding=_embed_with_retry(piece.content),
                embedding_model=settings.gemini_embedding_model,
            )
            for piece in pieces
        ]
        rag_chunk_repository.bulk_create(db, chunk_rows)
    except AppError as exc:
        db.rollback()
        document.status = RagDocumentStatus.FAILED
        document.error_message = exc.message
        document.chunk_count = 0
        rag_document_repository.update(db, document)
        raise

    document.status = RagDocumentStatus.INGESTED
    document.chunk_count = len(chunk_rows)
    document.error_message = None
    rag_document_repository.update(db, document)
    return document
