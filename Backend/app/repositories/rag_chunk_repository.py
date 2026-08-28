import math
import uuid

from pgvector.sqlalchemy import Vector as PgVector
from sqlalchemy import cast, delete, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.models.rag_document import RagDocument
from app.models.rag_document_chunk import RagDocumentChunk
from app.utils.enums import RagDocumentStatus

_EMBEDDING_DIM = get_settings().gemini_embedding_dimensions


def bulk_create(db: Session, chunks: list[RagDocumentChunk]) -> list[RagDocumentChunk]:
    db.add_all(chunks)
    db.flush()
    return chunks


def delete_by_document(db: Session, document_id: uuid.UUID) -> None:
    db.execute(delete(RagDocumentChunk).where(RagDocumentChunk.document_id == document_id))
    db.flush()


def list_by_document(db: Session, document_id: uuid.UUID) -> list[RagDocumentChunk]:
    stmt = (
        select(RagDocumentChunk)
        .where(RagDocumentChunk.document_id == document_id)
        .order_by(RagDocumentChunk.chunk_index)
    )
    return list(db.execute(stmt).scalars().all())


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def search(
    db: Session,
    query_vector: list[float],
    *,
    top_k: int,
    document_types: list | None = None,
    business_type: str | None = None,
) -> list[tuple[RagDocumentChunk, float]]:
    """Vector similarity search scoped to ingested/active documents. Returns
    (chunk, similarity_score) pairs, highest similarity first.

    On PostgreSQL this uses the real pgvector cosine-distance operator; the
    project's test suite runs against in-memory SQLite (app/tests/conftest.py),
    which has no vector extension, so this falls back to an equivalent
    Python-side cosine-similarity ranking there - the same dialect-conditional
    approach used for spatial queries in
    app/repositories/complaint_repository.py:list_within_radius.
    """
    base_stmt = (
        select(RagDocumentChunk)
        .join(RagDocument, RagDocumentChunk.document_id == RagDocument.id)
        .where(RagDocument.status == RagDocumentStatus.INGESTED, RagDocument.is_active.is_(True))
        .options(joinedload(RagDocumentChunk.document))
    )
    if document_types:
        base_stmt = base_stmt.where(RagDocument.document_type.in_(document_types))
    if business_type:
        base_stmt = base_stmt.where(
            (RagDocument.business_type == business_type) | (RagDocument.business_type.is_(None))
        )

    if db.bind is not None and db.bind.dialect.name == "postgresql":
        distance = RagDocumentChunk.embedding.op("<=>")(cast(query_vector, PgVector(_EMBEDDING_DIM)))
        stmt = base_stmt.order_by(distance).limit(top_k)
        chunks = list(db.execute(stmt).unique().scalars().all())
        # cosine distance = 1 - cosine similarity for pgvector's `<=>` operator;
        # ordering already came from the DB, this only recovers a similarity
        # score with a consistent meaning across both dialects.
        return [(chunk, _cosine_similarity(chunk.embedding, query_vector)) for chunk in chunks]

    candidates = list(db.execute(base_stmt).unique().scalars().all())
    scored = [(chunk, _cosine_similarity(chunk.embedding, query_vector)) for chunk in candidates]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:top_k]
