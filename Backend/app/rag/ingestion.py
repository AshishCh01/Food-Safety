"""Ingestion orchestration: parse -> chunk -> embed -> store
(docs/RAG_ARCHITECTURE.md section 4). Runs synchronously from the admin ingest
endpoint, matching the existing synchronous-agent-call pattern used by
Complaint Triage / Evidence Analysis (an explicit POST triggers the run; no
background queue exists in this phase).

Embedding is the slow part - one Gemini API round-trip per chunk, and on a
free-tier API key the project-wide rate limit is low enough that even a
handful of back-to-back calls trips a 429. So chunks are embedded fully
sequentially with a fixed pacing delay between calls (deliberately trading
ingestion speed for reliability), plus patient exponential-backoff retries
for the occasional 429 that still gets through.
"""

import random
import time

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.rag_document import RagDocument
from app.models.rag_document_chunk import RagDocumentChunk
from app.rag import chunking, parsing
from app.rag.chunking import Chunk
from app.repositories import rag_chunk_repository, rag_document_repository
from app.services import ai_service
from app.utils.enums import RagDocumentStatus
from app.utils.exceptions import AppError, GeminiRateLimitedError, GeminiUnavailableError, RagIngestionError

# A large document (e.g. a full legal Act) can chunk into 100+ pieces, each
# needing its own Gemini embedding call - at that volume, hitting a 429 at
# least once is the normal case, not the exception. So this retries more
# patiently (exponential backoff + jitter) than the single-call agents
# (complaint triage, evidence analysis) do, where a human is waiting
# synchronously on one request.
_MAX_EMBED_ATTEMPTS = 6
_RETRY_BASE_SECONDS = 2.0
_RETRY_MAX_BACKOFF_SECONDS = 30.0
_RETRYABLE_EXCEPTIONS = (GeminiRateLimitedError, GeminiUnavailableError)

# Minimum gap between the *start* of one embedding call and the next, so
# ingestion behaves like a slow trickle instead of a burst - the actual
# cause of the 429s seen on a free-tier key, not raw call volume.
_MIN_CALL_INTERVAL_SECONDS = 2.0


def _embed_with_retry(text: str) -> list[float]:
    for attempt in range(1, _MAX_EMBED_ATTEMPTS + 1):
        try:
            return ai_service.embed_text(text)
        except _RETRYABLE_EXCEPTIONS:
            if attempt < _MAX_EMBED_ATTEMPTS:
                backoff = min(_RETRY_BASE_SECONDS * (2 ** (attempt - 1)), _RETRY_MAX_BACKOFF_SECONDS)
                time.sleep(backoff + random.uniform(0, backoff * 0.25))
                continue
            raise
    raise AssertionError("unreachable")  # pragma: no cover


def _embed_all(pieces: list[Chunk]) -> list[list[float]]:
    """Embeds every chunk one at a time, in order, pacing the start of each
    call at least `_MIN_CALL_INTERVAL_SECONDS` apart."""
    embeddings: list[list[float]] = []
    for piece in pieces:
        if embeddings:
            time.sleep(_MIN_CALL_INTERVAL_SECONDS)
        embeddings.append(_embed_with_retry(piece.content))
    return embeddings


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

        embeddings = _embed_all(pieces)
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
                embedding=embedding,
                embedding_model=settings.gemini_embedding_model,
            )
            for piece, embedding in zip(pieces, embeddings)
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
