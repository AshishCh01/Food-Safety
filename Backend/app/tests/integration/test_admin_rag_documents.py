from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services import ai_service, storage_service
from app.tests.factories import auth_headers, create_district, create_division, create_staff, create_user
from app.utils.enums import UserRole


def _admin_headers(db_session: Session) -> dict:
    admin = create_user(db_session, email="root-admin@example.com", role=UserRole.ADMIN)
    return auth_headers(admin)


def _patch_storage(monkeypatch) -> dict:
    store: dict = {}

    def _upload(bucket, path, content, content_type):
        store[(bucket, path)] = content
        return path

    def _download(bucket, path):
        return store[(bucket, path)]

    monkeypatch.setattr(storage_service, "upload_file", _upload)
    monkeypatch.setattr(storage_service, "download_file", _download)
    return store


def test_admin_can_upload_document(client: TestClient, db_session: Session, monkeypatch) -> None:
    _patch_storage(monkeypatch)

    response = client.post(
        "/api/v1/admin/rag/documents",
        headers=_admin_headers(db_session),
        data={"title": "FSSAI Act 2006", "document_type": "law", "source_organization": "FSSAI"},
        files={"file": ("act.txt", b"Section 1: definitions.", "text/plain")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["title"] == "FSSAI Act 2006"
    assert body["chunk_count"] == 0


def test_non_admin_cannot_upload_document(client: TestClient, db_session: Session, monkeypatch) -> None:
    _patch_storage(monkeypatch)
    division = create_division(db_session)
    district = create_district(db_session, division)
    inspector_user, _ = create_staff(
        db_session, district, role=UserRole.INSPECTOR, email="inspector@example.com", employee_code="INS-1"
    )

    response = client.post(
        "/api/v1/admin/rag/documents",
        headers=auth_headers(inspector_user, district_id=district.id),
        data={"title": "Doc", "document_type": "law"},
        files={"file": ("act.txt", b"content", "text/plain")},
    )

    assert response.status_code == 403


def test_duplicate_checksum_upload_returns_conflict(client: TestClient, db_session: Session, monkeypatch) -> None:
    _patch_storage(monkeypatch)
    headers = _admin_headers(db_session)
    content = b"Identical content for dedup test."
    client.post(
        "/api/v1/admin/rag/documents",
        headers=headers,
        data={"title": "Doc A", "document_type": "law"},
        files={"file": ("a.txt", content, "text/plain")},
    )

    response = client.post(
        "/api/v1/admin/rag/documents",
        headers=headers,
        data={"title": "Doc B", "document_type": "regulation"},
        files={"file": ("b.txt", content, "text/plain")},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "RAG_DOCUMENT_DUPLICATE"


def test_list_and_get_document(client: TestClient, db_session: Session, monkeypatch) -> None:
    _patch_storage(monkeypatch)
    headers = _admin_headers(db_session)
    upload = client.post(
        "/api/v1/admin/rag/documents",
        headers=headers,
        data={"title": "Doc C", "document_type": "hygiene_guideline"},
        files={"file": ("c.txt", b"hygiene content", "text/plain")},
    )
    document_id = upload.json()["id"]

    list_response = client.get("/api/v1/admin/rag/documents", headers=headers)
    get_response = client.get(f"/api/v1/admin/rag/documents/{document_id}", headers=headers)

    assert list_response.status_code == 200
    assert list_response.json()["total"] >= 1
    assert get_response.status_code == 200
    assert get_response.json()["id"] == document_id


def test_get_unknown_document_returns_404(client: TestClient, db_session: Session) -> None:
    response = client.get(
        "/api/v1/admin/rag/documents/00000000-0000-0000-0000-000000000000",
        headers=_admin_headers(db_session),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RAG_DOCUMENT_NOT_FOUND"


def test_ingest_endpoint_marks_document_ingested(client: TestClient, db_session: Session, monkeypatch) -> None:
    _patch_storage(monkeypatch)
    monkeypatch.setattr(ai_service, "embed_text", lambda text: [0.1, 0.2, 0.3])
    headers = _admin_headers(db_session)
    upload = client.post(
        "/api/v1/admin/rag/documents",
        headers=headers,
        data={"title": "Doc D", "document_type": "law"},
        files={"file": ("d.txt", b"# Rules\n\nDo not sell expired food.", "text/plain")},
    )
    document_id = upload.json()["id"]

    response = client.post(f"/api/v1/admin/rag/documents/{document_id}/ingest", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ingested"
    assert body["chunk_count"] >= 1


def test_ingest_endpoint_marks_document_failed_on_embedding_error(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    from app.utils.exceptions import GeminiRequestError

    _patch_storage(monkeypatch)

    def _raise(_text):
        raise GeminiRequestError("bad request")

    monkeypatch.setattr(ai_service, "embed_text", _raise)
    headers = _admin_headers(db_session)
    upload = client.post(
        "/api/v1/admin/rag/documents",
        headers=headers,
        data={"title": "Doc F", "document_type": "law"},
        files={"file": ("f.txt", b"content that will fail to embed", "text/plain")},
    )
    document_id = upload.json()["id"]

    response = client.post(f"/api/v1/admin/rag/documents/{document_id}/ingest", headers=headers)

    assert response.status_code == 502
    get_response = client.get(f"/api/v1/admin/rag/documents/{document_id}", headers=headers)
    assert get_response.json()["status"] == "failed"


def test_deactivate_endpoint_sets_is_active_false(client: TestClient, db_session: Session, monkeypatch) -> None:
    _patch_storage(monkeypatch)
    headers = _admin_headers(db_session)
    upload = client.post(
        "/api/v1/admin/rag/documents",
        headers=headers,
        data={"title": "Doc E", "document_type": "law"},
        files={"file": ("e.txt", b"content", "text/plain")},
    )
    document_id = upload.json()["id"]

    response = client.post(f"/api/v1/admin/rag/documents/{document_id}/deactivate", headers=headers)

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_unauthenticated_cannot_list_documents(client: TestClient) -> None:
    response = client.get("/api/v1/admin/rag/documents")

    assert response.status_code == 401
