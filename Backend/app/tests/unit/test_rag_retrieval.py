import pytest
from sqlalchemy.orm import Session

from app.rag import retrieval
from app.repositories import rag_chunk_repository
from app.services import ai_service
from app.tests.factories import create_rag_chunk, create_rag_document, create_user
from app.utils.enums import RagDocumentStatus, RagDocumentType
from app.utils.exceptions import GeminiUnavailableError


def test_search_ranks_by_cosine_similarity(db_session: Session) -> None:
    uploader = create_user(db_session, email="admin@example.com")
    document = create_rag_document(db_session, uploader, status=RagDocumentStatus.INGESTED)
    close = create_rag_chunk(db_session, document, chunk_index=0, embedding=[1.0, 0.0, 0.0], content="close match")
    far = create_rag_chunk(db_session, document, chunk_index=1, embedding=[0.0, 1.0, 0.0], content="far match")

    results = rag_chunk_repository.search(db_session, [1.0, 0.0, 0.0], top_k=5)

    assert [chunk.id for chunk, _ in results] == [close.id, far.id]


def test_search_only_considers_ingested_active_documents(db_session: Session) -> None:
    uploader = create_user(db_session, email="admin2@example.com")
    pending_doc = create_rag_document(db_session, uploader, status=RagDocumentStatus.PENDING)
    create_rag_chunk(db_session, pending_doc, embedding=[1.0, 0.0, 0.0])
    inactive_doc = create_rag_document(db_session, uploader, status=RagDocumentStatus.INGESTED, is_active=False)
    create_rag_chunk(db_session, inactive_doc, embedding=[1.0, 0.0, 0.0])

    results = rag_chunk_repository.search(db_session, [1.0, 0.0, 0.0], top_k=5)

    assert results == []


def test_search_filters_by_document_type(db_session: Session) -> None:
    uploader = create_user(db_session, email="admin3@example.com")
    law_doc = create_rag_document(
        db_session, uploader, status=RagDocumentStatus.INGESTED, document_type=RagDocumentType.LAW
    )
    law_chunk = create_rag_chunk(db_session, law_doc, embedding=[1.0, 0.0, 0.0])
    guideline_doc = create_rag_document(
        db_session, uploader, status=RagDocumentStatus.INGESTED, document_type=RagDocumentType.INSPECTION_GUIDELINE
    )
    create_rag_chunk(db_session, guideline_doc, embedding=[1.0, 0.0, 0.0])

    results = rag_chunk_repository.search(db_session, [1.0, 0.0, 0.0], top_k=5, document_types=[RagDocumentType.LAW])

    assert [chunk.id for chunk, _ in results] == [law_chunk.id]


def test_search_filters_by_business_type_or_null(db_session: Session) -> None:
    uploader = create_user(db_session, email="admin4@example.com")
    restaurant_doc = create_rag_document(
        db_session, uploader, status=RagDocumentStatus.INGESTED, business_type="restaurant"
    )
    restaurant_chunk = create_rag_chunk(db_session, restaurant_doc, embedding=[1.0, 0.0, 0.0])
    dairy_doc = create_rag_document(db_session, uploader, status=RagDocumentStatus.INGESTED, business_type="dairy")
    create_rag_chunk(db_session, dairy_doc, embedding=[1.0, 0.0, 0.0])
    general_doc = create_rag_document(db_session, uploader, status=RagDocumentStatus.INGESTED, business_type=None)
    general_chunk = create_rag_chunk(db_session, general_doc, embedding=[1.0, 0.0, 0.0])

    results = rag_chunk_repository.search(db_session, [1.0, 0.0, 0.0], top_k=5, business_type="restaurant")

    ids = {chunk.id for chunk, _ in results}
    assert ids == {restaurant_chunk.id, general_chunk.id}


def test_search_respects_top_k(db_session: Session) -> None:
    uploader = create_user(db_session, email="admin5@example.com")
    document = create_rag_document(db_session, uploader, status=RagDocumentStatus.INGESTED)
    for i in range(5):
        create_rag_chunk(db_session, document, chunk_index=i, embedding=[1.0, 0.0, 0.0])

    results = rag_chunk_repository.search(db_session, [1.0, 0.0, 0.0], top_k=2)

    assert len(results) == 2


def test_empty_knowledge_base_returns_empty_list(db_session: Session) -> None:
    results = rag_chunk_repository.search(db_session, [1.0, 0.0, 0.0], top_k=5)

    assert results == []


def test_retrieval_search_embeds_query_and_returns_citable_chunks(db_session: Session, monkeypatch) -> None:
    monkeypatch.setattr(ai_service, "embed_text", lambda text: [1.0, 0.0, 0.0])
    uploader = create_user(db_session, email="admin6@example.com")
    document = create_rag_document(db_session, uploader, status=RagDocumentStatus.INGESTED, title="FSSAI Act 2006")
    create_rag_chunk(db_session, document, embedding=[1.0, 0.0, 0.0], page_number=12, section_title="Hygiene")

    results = retrieval.search(db_session, "hand washing requirements", top_k=3)

    assert len(results) == 1
    assert results[0].document_title == "FSSAI Act 2006"
    assert results[0].page_number == 12
    assert results[0].section_title == "Hygiene"


def test_retrieval_search_propagates_embedding_failure(db_session: Session, monkeypatch) -> None:
    def _raise(_text):
        raise GeminiUnavailableError()

    monkeypatch.setattr(ai_service, "embed_text", _raise)

    with pytest.raises(GeminiUnavailableError):
        retrieval.search(db_session, "any query", top_k=3)
