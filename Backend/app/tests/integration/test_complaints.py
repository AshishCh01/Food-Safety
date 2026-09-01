from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services import storage_service
from app.tests.factories import (
    auth_headers,
    create_complaint_category,
    create_district,
    create_division,
    create_user,
)

# Real JPEG magic bytes so upload requests pass content-sniffing validation
# (app/utils/validators.py) rather than only the declared Content-Type.
FAKE_JPEG_BYTES = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01" + b"fake-image-bytes"


def _setup(db_session: Session):
    division = create_division(db_session, name="Pune Division", code="PUN")
    district = create_district(db_session, division, name="Pune", code="PUN")
    category = create_complaint_category(db_session, key="expired_food", name="Expired Food")
    citizen = create_user(db_session, email="citizen@example.com", full_name="Asha Citizen")
    return division, district, category, citizen


def _complaint_payload(district_id, category_id) -> dict:
    return {
        "category_id": str(category_id),
        "district_id": str(district_id),
        "title": "Expired dairy products on sale",
        "description": "Found expired milk packets still being sold at the counter this morning.",
        "priority": "high",
        "address_line": "Shop 4, FC Road",
        "business": {
            "business_name": "Green Grocers",
            "business_type": "grocery",
            "address": "Shop 4, FC Road, Pune",
        },
    }


def test_create_complaint_success(client: TestClient, db_session: Session) -> None:
    _, district, category, citizen = _setup(db_session)

    response = client.post(
        "/api/v1/complaints",
        json=_complaint_payload(district.id, category.id),
        headers=auth_headers(citizen),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["complaint_number"].startswith(f"MH-{district.code}-")
    assert body["complaint_number"].endswith("000001")
    assert body["status"] == "submitted"
    assert body["priority"] == "high"
    assert body["business"]["business_name"] == "Green Grocers"
    assert body["submitted_by_user_id"] == str(citizen.id)


def test_complaint_numbers_increment_per_district_per_year(client: TestClient, db_session: Session) -> None:
    _, district, category, citizen = _setup(db_session)
    payload = _complaint_payload(district.id, category.id)

    first = client.post("/api/v1/complaints", json=payload, headers=auth_headers(citizen)).json()
    second = client.post("/api/v1/complaints", json=payload, headers=auth_headers(citizen)).json()

    assert first["complaint_number"] != second["complaint_number"]
    assert second["complaint_number"].endswith("000002")


def test_create_complaint_unknown_category_returns_404(client: TestClient, db_session: Session) -> None:
    _, district, category, citizen = _setup(db_session)
    payload = _complaint_payload(district.id, category.id)
    payload["category_id"] = "00000000-0000-0000-0000-000000000000"

    response = client.post("/api/v1/complaints", json=payload, headers=auth_headers(citizen))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CATEGORY_NOT_FOUND"


def test_create_complaint_validation_error(client: TestClient, db_session: Session) -> None:
    _, district, category, citizen = _setup(db_session)
    payload = _complaint_payload(district.id, category.id)
    payload["title"] = "ab"  # below min_length=3

    response = client.post("/api/v1/complaints", json=payload, headers=auth_headers(citizen))

    assert response.status_code == 422


def test_business_is_reused_for_matching_name_and_address(client: TestClient, db_session: Session) -> None:
    _, district, category, citizen = _setup(db_session)
    payload = _complaint_payload(district.id, category.id)

    first = client.post("/api/v1/complaints", json=payload, headers=auth_headers(citizen)).json()
    second = client.post("/api/v1/complaints", json=payload, headers=auth_headers(citizen)).json()

    assert first["business"]["id"] == second["business"]["id"]


def test_list_my_complaints_and_filter(client: TestClient, db_session: Session) -> None:
    _, district, category, citizen = _setup(db_session)
    other_category = create_complaint_category(db_session, key="contamination", name="Contamination")
    payload = _complaint_payload(district.id, category.id)
    client.post("/api/v1/complaints", json=payload, headers=auth_headers(citizen))

    other_payload = _complaint_payload(district.id, other_category.id)
    client.post("/api/v1/complaints", json=other_payload, headers=auth_headers(citizen))

    response = client.get("/api/v1/complaints/my", headers=auth_headers(citizen))
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2

    filtered = client.get(
        "/api/v1/complaints/my",
        params={"category_id": str(category.id)},
        headers=auth_headers(citizen),
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1


def test_get_complaint_detail_and_timeline(client: TestClient, db_session: Session) -> None:
    _, district, category, citizen = _setup(db_session)
    created = client.post(
        "/api/v1/complaints", json=_complaint_payload(district.id, category.id), headers=auth_headers(citizen)
    ).json()

    detail = client.get(f"/api/v1/complaints/{created['id']}", headers=auth_headers(citizen))
    assert detail.status_code == 200
    assert detail.json()["id"] == created["id"]

    timeline = client.get(f"/api/v1/complaints/{created['id']}/timeline", headers=auth_headers(citizen))
    assert timeline.status_code == 200
    entries = timeline.json()
    assert len(entries) == 1
    assert entries[0]["old_status"] is None
    assert entries[0]["new_status"] == "submitted"


def test_citizen_cannot_access_another_citizens_complaint(client: TestClient, db_session: Session) -> None:
    _, district, category, citizen = _setup(db_session)
    other_citizen = create_user(db_session, email="other@example.com", full_name="Other Citizen")
    created = client.post(
        "/api/v1/complaints", json=_complaint_payload(district.id, category.id), headers=auth_headers(citizen)
    ).json()

    response = client.get(f"/api/v1/complaints/{created['id']}", headers=auth_headers(other_citizen))

    assert response.status_code == 404


def test_upload_evidence_success(client: TestClient, db_session: Session, monkeypatch) -> None:
    _, district, category, citizen = _setup(db_session)
    created = client.post(
        "/api/v1/complaints", json=_complaint_payload(district.id, category.id), headers=auth_headers(citizen)
    ).json()

    monkeypatch.setattr(storage_service, "upload_file", lambda bucket, path, content, content_type: path)

    response = client.post(
        f"/api/v1/complaints/{created['id']}/evidence",
        headers=auth_headers(citizen),
        files={"file": ("photo.jpg", FAKE_JPEG_BYTES, "image/jpeg")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["file_name"] == "photo.jpg"
    assert body["file_type"] == "image/jpeg"
    assert body["file_size"] == len(FAKE_JPEG_BYTES)
    assert len(body["checksum"]) == 64


def test_evidence_upload_is_rate_limited_after_repeated_attempts(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    from app.core.rate_limit import citizen_evidence_upload_rate_limiter

    _, district, category, citizen = _setup(db_session)
    created = client.post(
        "/api/v1/complaints", json=_complaint_payload(district.id, category.id), headers=auth_headers(citizen)
    ).json()

    monkeypatch.setattr(storage_service, "upload_file", lambda bucket, path, content, content_type: path)

    responses = [
        client.post(
            f"/api/v1/complaints/{created['id']}/evidence",
            headers=auth_headers(citizen),
            files={"file": ("photo.jpg", FAKE_JPEG_BYTES, "image/jpeg")},
        )
        for _ in range(citizen_evidence_upload_rate_limiter.max_requests + 1)
    ]

    assert all(r.status_code == 201 for r in responses[:-1])
    assert responses[-1].status_code == 429
    assert responses[-1].json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"


def test_upload_evidence_rejects_unsupported_type(client: TestClient, db_session: Session, monkeypatch) -> None:
    _, district, category, citizen = _setup(db_session)
    created = client.post(
        "/api/v1/complaints", json=_complaint_payload(district.id, category.id), headers=auth_headers(citizen)
    ).json()

    monkeypatch.setattr(storage_service, "upload_file", lambda bucket, path, content, content_type: path)

    response = client.post(
        f"/api/v1/complaints/{created['id']}/evidence",
        headers=auth_headers(citizen),
        files={"file": ("notes.txt", b"plain text", "text/plain")},
    )

    assert response.status_code == 415


def test_list_evidence_returns_signed_urls(client: TestClient, db_session: Session, monkeypatch) -> None:
    _, district, category, citizen = _setup(db_session)
    created = client.post(
        "/api/v1/complaints", json=_complaint_payload(district.id, category.id), headers=auth_headers(citizen)
    ).json()

    monkeypatch.setattr(storage_service, "upload_file", lambda bucket, path, content, content_type: path)
    monkeypatch.setattr(
        storage_service, "create_signed_url", lambda bucket, path, expires_in=300: f"https://signed.example/{path}"
    )

    client.post(
        f"/api/v1/complaints/{created['id']}/evidence",
        headers=auth_headers(citizen),
        files={"file": ("photo.jpg", FAKE_JPEG_BYTES, "image/jpeg")},
    )

    response = client.get(f"/api/v1/complaints/{created['id']}/evidence", headers=auth_headers(citizen))

    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["download_url"].startswith("https://signed.example/")
