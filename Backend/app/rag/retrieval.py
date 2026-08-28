"""Retrieval over the RAG knowledge base (docs/RAG_ARCHITECTURE.md sections
8-9). Embeds a query and returns ranked, citable chunks scoped to
ingested/active documents only. An empty result list is a normal outcome, not
an error - callers must not fabricate an answer when nothing relevant is
found. Gemini embedding failures propagate as the existing
GeminiRateLimitedError/GeminiUnavailableError/GeminiRequestError for the
caller to handle without inventing an answer.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.repositories import rag_chunk_repository
from app.services import ai_service
from app.utils.enums import RagDocumentType


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    document_title: str
    source_organization: str | None
    document_type: str
    page_number: int | None
    section_title: str | None
    content: str
    score: float


def search(
    db: Session,
    query: str,
    *,
    top_k: int | None = None,
    document_types: list[RagDocumentType] | None = None,
    business_type: str | None = None,
) -> list[RetrievedChunk]:
    settings = get_settings()
    query_vector = ai_service.embed_text(query)
    results = rag_chunk_repository.search(
        db,
        query_vector,
        top_k=top_k or settings.rag_retrieval_top_k,
        document_types=document_types,
        business_type=business_type,
    )
    return [
        RetrievedChunk(
            chunk_id=str(chunk.id),
            document_id=str(chunk.document_id),
            document_title=chunk.document.title,
            source_organization=chunk.document.source_organization,
            document_type=chunk.document.document_type.value,
            page_number=chunk.page_number,
            section_title=chunk.section_title,
            content=chunk.content,
            score=score,
        )
        for chunk, score in results
    ]
