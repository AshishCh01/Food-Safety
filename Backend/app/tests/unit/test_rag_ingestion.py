import pytest
from sqlalchemy.orm import Session

from app.rag import ingestion
from app.repositories import rag_chunk_repository, rag_document_repository
from app.services import ai_service
from app.tests.factories import create_rag_document, create_user
from app.utils.enums import RagDocumentStatus
from app.utils.exceptions import GeminiUnavailableError, RagIngestionError, UnsupportedFileTypeError


def _fake_embedding(_text: str) -> list[float]:
    return [0.1, 0.2, 0.3]


def test_ingest_text_document_creates_chunks_and_marks_ingested(db_session: Session, monkeypatch) -> None:
    monkeypatch.setattr(ai_service, "embed_text", _fake_embedding)
    uploader = create_user(db_session, email="admin@example.com")
    document = create_rag_document(db_session, uploader, file_type="text/plain")

    result = ingestion.ingest_document(db_session, document, b"# Hygiene\n\nWash hands before handling food.")

    assert result.status == RagDocumentStatus.INGESTED
    assert result.chunk_count == 1
    chunks = rag_chunk_repository.list_by_document(db_session, document.id)
    assert len(chunks) == 1
    assert chunks[0].section_title == "Hygiene"
    assert chunks[0].embedding == [0.1, 0.2, 0.3]
    assert chunks[0].chunk_metadata["document_type"] == document.document_type.value


def test_ingest_unsupported_file_type_marks_failed_without_calling_embed(db_session: Session, monkeypatch) -> None:
    def _fail(_text):
        raise AssertionError("embed_text should not be called")

    monkeypatch.setattr(ai_service, "embed_text", _fail)
    uploader = create_user(db_session, email="admin2@example.com")
    document = create_rag_document(db_session, uploader, file_type="video/mp4")

    with pytest.raises(UnsupportedFileTypeError):
        ingestion.ingest_document(db_session, document, b"data")

    refreshed = rag_document_repository.get_by_id(db_session, document.id)
    assert refreshed.status == RagDocumentStatus.FAILED
    assert refreshed.chunk_count == 0
    assert refreshed.error_message


def test_ingest_embedding_failure_leaves_no_partial_chunks(db_session: Session, monkeypatch) -> None:
    calls = {"count": 0}

    def _flaky(_text):
        calls["count"] += 1
        if calls["count"] >= 2:
            raise GeminiUnavailableError()
        return [0.1, 0.2, 0.3]

    monkeypatch.setattr(ai_service, "embed_text", _flaky)
    monkeypatch.setattr(ingestion.time, "sleep", lambda *a, **k: None)
    uploader = create_user(db_session, email="admin3@example.com")
    document = create_rag_document(db_session, uploader, file_type="text/plain")
    text = "# One\n\nFirst section text.\n\n# Two\n\nSecond section text."

    with pytest.raises(GeminiUnavailableError):
        ingestion.ingest_document(db_session, document, text.encode())

    refreshed = rag_document_repository.get_by_id(db_session, document.id)
    assert refreshed.status == RagDocumentStatus.FAILED
    assert rag_chunk_repository.list_by_document(db_session, document.id) == []


def test_ingest_empty_document_raises_and_marks_failed(db_session: Session, monkeypatch) -> None:
    monkeypatch.setattr(ai_service, "embed_text", _fake_embedding)
    uploader = create_user(db_session, email="admin4@example.com")
    document = create_rag_document(db_session, uploader, file_type="text/plain")

    with pytest.raises(RagIngestionError):
        ingestion.ingest_document(db_session, document, b"   \n  ")

    refreshed = rag_document_repository.get_by_id(db_session, document.id)
    assert refreshed.status == RagDocumentStatus.FAILED


def test_reingest_replaces_existing_chunks(db_session: Session, monkeypatch) -> None:
    monkeypatch.setattr(ai_service, "embed_text", _fake_embedding)
    uploader = create_user(db_session, email="admin5@example.com")
    document = create_rag_document(db_session, uploader, file_type="text/plain")
    ingestion.ingest_document(db_session, document, b"# A\n\nFirst version text.")

    ingestion.ingest_document(db_session, document, b"# A\n\nFirst.\n\n# B\n\nSecond.")

    refreshed = rag_document_repository.get_by_id(db_session, document.id)
    assert refreshed.chunk_count == 2
    chunks = rag_chunk_repository.list_by_document(db_session, document.id)
    assert len(chunks) == 2
