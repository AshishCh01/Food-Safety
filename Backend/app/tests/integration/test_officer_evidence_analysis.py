import json

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.agents.evidence_analysis import agent as evidence_analysis_agent
from app.services import ai_service, evidence_service
from app.tests.factories import (
    auth_headers,
    create_business,
    create_complaint,
    create_complaint_category,
    create_district,
    create_division,
    create_evidence,
    create_staff,
    create_user,
)
from app.utils.enums import UserRole
from app.utils.exceptions import GeminiUnavailableError

_FAKE_IMAGE_BYTES = b"\xff\xd8\xff\xe0fake-jpeg-bytes"


def _valid_payload(**overrides) -> str:
    payload = {
        "extracted_text": "Shree Dairy Toned Milk EXP 01/2027",
        "product_name": "Toned Milk",
        "manufacturer": "Shree Dairy",
        "batch_lot_number": "B12345",
        "manufacturing_date_text": "01/2026",
        "expiry_date_text": "01/2027",
        "packaging_observations": "Packet is sealed and intact.",
        "hygiene_observations": None,
        "foreign_object_observations": None,
        "confidence": 0.85,
        "uncertainty_notes": [],
    }
    payload.update(overrides)
    return json.dumps(payload)


def _setup(db_session: Session):
    division = create_division(db_session, name="Pune Division", code="PUN")
    pune = create_district(db_session, division, name="Pune", code="PUN")
    nagpur = create_district(db_session, division, name="Nagpur", code="NGP")

    pune_officer, _ = create_staff(
        db_session, pune, role=UserRole.DISTRICT_OFFICER, email="pune.officer@example.com", employee_code="DO-PUN"
    )
    _nagpur_officer, _ = create_staff(
        db_session, nagpur, role=UserRole.DISTRICT_OFFICER, email="nagpur.officer@example.com", employee_code="DO-NGP"
    )
    pune_inspector, _ = create_staff(
        db_session, pune, role=UserRole.INSPECTOR, email="pune.inspector@example.com", employee_code="INS-PUN"
    )

    category = create_complaint_category(db_session, key="expired_food", name="Expired Food")
    citizen = create_user(db_session, email="citizen@example.com", full_name="Asha Citizen")
    business = create_business(db_session, pune, business_name="Shree Dairy")

    pune_complaint = create_complaint(
        db_session, citizen, pune, category, business=business, complaint_number="MH-PUN-2026-000001"
    )
    nagpur_complaint = create_complaint(db_session, citizen, nagpur, category, complaint_number="MH-NGP-2026-000001")
    pune_evidence = create_evidence(db_session, pune_complaint, citizen)

    return pune_officer, pune_inspector, pune_complaint, pune_evidence, nagpur_complaint


def _patch_bytes(monkeypatch) -> None:
    monkeypatch.setattr(evidence_service, "get_evidence_bytes", lambda evidence: _FAKE_IMAGE_BYTES)


def test_officer_can_run_analysis_for_own_district_evidence(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    pune_officer, _inspector, pune_complaint, evidence, _nagpur_complaint = _setup(db_session)
    _patch_bytes(monkeypatch)
    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", lambda *a, **k: _valid_payload())

    response = client.post(
        f"/api/v1/officer/complaints/{pune_complaint.id}/evidence/{evidence.id}/analysis",
        headers=auth_headers(pune_officer),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["product_name"] == "Toned Milk"
    assert body["manufacturer"] == "Shree Dairy"
    assert body["possible_expired"] is False
    assert body["is_uncertain"] is False


def test_officer_cannot_analyze_evidence_from_another_districts_complaint(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    pune_officer, _inspector, _pune_complaint, evidence, nagpur_complaint = _setup(db_session)
    _patch_bytes(monkeypatch)
    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", lambda *a, **k: _valid_payload())

    response = client.post(
        f"/api/v1/officer/complaints/{nagpur_complaint.id}/evidence/{evidence.id}/analysis",
        headers=auth_headers(pune_officer),
    )

    assert response.status_code == 404


def test_get_analysis_returns_404_before_any_run(client: TestClient, db_session: Session) -> None:
    pune_officer, _inspector, pune_complaint, evidence, _nagpur_complaint = _setup(db_session)

    response = client.get(
        f"/api/v1/officer/complaints/{pune_complaint.id}/evidence/{evidence.id}/analysis",
        headers=auth_headers(pune_officer),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "EVIDENCE_ANALYSIS_NOT_FOUND"


def test_get_analysis_returns_cached_result_without_calling_gemini_again(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    pune_officer, _inspector, pune_complaint, evidence, _nagpur_complaint = _setup(db_session)
    _patch_bytes(monkeypatch)
    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", lambda *a, **k: _valid_payload())

    post_response = client.post(
        f"/api/v1/officer/complaints/{pune_complaint.id}/evidence/{evidence.id}/analysis",
        headers=auth_headers(pune_officer),
    )
    assert post_response.status_code == 200

    def _fail_if_called(*a, **k):
        raise AssertionError("GET should not call Gemini")

    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", _fail_if_called)

    get_response = client.get(
        f"/api/v1/officer/complaints/{pune_complaint.id}/evidence/{evidence.id}/analysis",
        headers=auth_headers(pune_officer),
    )

    assert get_response.status_code == 200
    assert get_response.json()["product_name"] == post_response.json()["product_name"]


def test_post_without_force_does_not_recall_gemini_after_completed_run(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    pune_officer, _inspector, pune_complaint, evidence, _nagpur_complaint = _setup(db_session)
    _patch_bytes(monkeypatch)
    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", lambda *a, **k: _valid_payload())

    first = client.post(
        f"/api/v1/officer/complaints/{pune_complaint.id}/evidence/{evidence.id}/analysis",
        headers=auth_headers(pune_officer),
    )
    assert first.status_code == 200

    def _fail_if_called(*a, **k):
        raise AssertionError("POST without force should not call Gemini again")

    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", _fail_if_called)

    second = client.post(
        f"/api/v1/officer/complaints/{pune_complaint.id}/evidence/{evidence.id}/analysis",
        headers=auth_headers(pune_officer),
    )
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]


def test_post_with_force_calls_gemini_again(client: TestClient, db_session: Session, monkeypatch) -> None:
    pune_officer, _inspector, pune_complaint, evidence, _nagpur_complaint = _setup(db_session)
    _patch_bytes(monkeypatch)
    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", lambda *a, **k: _valid_payload())

    first = client.post(
        f"/api/v1/officer/complaints/{pune_complaint.id}/evidence/{evidence.id}/analysis",
        headers=auth_headers(pune_officer),
    )
    assert first.status_code == 200

    calls = {"count": 0}

    def _rerun(*a, **k):
        calls["count"] += 1
        return _valid_payload(product_name="Re-analyzed")

    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", _rerun)

    second = client.post(
        f"/api/v1/officer/complaints/{pune_complaint.id}/evidence/{evidence.id}/analysis?force=true",
        headers=auth_headers(pune_officer),
    )

    assert second.status_code == 200
    assert calls["count"] == 1
    assert second.json()["id"] != first.json()["id"]
    assert second.json()["product_name"] == "Re-analyzed"


def test_inspector_cannot_run_officer_evidence_analysis_endpoint(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    pune_officer, pune_inspector, pune_complaint, evidence, _nagpur_complaint = _setup(db_session)
    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", lambda *a, **k: _valid_payload())

    response = client.post(
        f"/api/v1/officer/complaints/{pune_complaint.id}/evidence/{evidence.id}/analysis",
        headers=auth_headers(pune_inspector),
    )

    assert response.status_code == 403


def test_unauthenticated_request_is_rejected(client: TestClient, db_session: Session) -> None:
    _officer, _inspector, pune_complaint, evidence, _nagpur_complaint = _setup(db_session)

    response = client.post(
        f"/api/v1/officer/complaints/{pune_complaint.id}/evidence/{evidence.id}/analysis"
    )

    assert response.status_code == 401


def test_evidence_not_belonging_to_complaint_returns_404(client: TestClient, db_session: Session) -> None:
    pune_officer, _inspector, pune_complaint, _evidence, nagpur_complaint = _setup(db_session)
    citizen = create_user(db_session, email="other.citizen@example.com", full_name="Other Citizen")
    other_evidence = create_evidence(db_session, nagpur_complaint, citizen)

    response = client.get(
        f"/api/v1/officer/complaints/{pune_complaint.id}/evidence/{other_evidence.id}/analysis",
        headers=auth_headers(pune_officer),
    )

    assert response.status_code == 404


def test_gemini_failure_returns_service_unavailable_and_persists_failure(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    pune_officer, _inspector, pune_complaint, evidence, _nagpur_complaint = _setup(db_session)
    _patch_bytes(monkeypatch)

    def _raise(*a, **k):
        raise GeminiUnavailableError()

    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", _raise)
    monkeypatch.setattr(evidence_analysis_agent.time, "sleep", lambda *a, **k: None)

    response = client.post(
        f"/api/v1/officer/complaints/{pune_complaint.id}/evidence/{evidence.id}/analysis",
        headers=auth_headers(pune_officer),
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "GEMINI_UNAVAILABLE"

    get_response = client.get(
        f"/api/v1/officer/complaints/{pune_complaint.id}/evidence/{evidence.id}/analysis",
        headers=auth_headers(pune_officer),
    )
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "failed"
    assert get_response.json()["error_code"] == "GEMINI_UNAVAILABLE"


def test_unsupported_evidence_file_type_returns_415(client: TestClient, db_session: Session) -> None:
    pune_officer, _inspector, pune_complaint, _evidence, _nagpur_complaint = _setup(db_session)
    citizen = create_user(db_session, email="video.citizen@example.com", full_name="Video Citizen")
    video_evidence = create_evidence(db_session, pune_complaint, citizen, file_type="video/mp4")

    response = client.post(
        f"/api/v1/officer/complaints/{pune_complaint.id}/evidence/{video_evidence.id}/analysis",
        headers=auth_headers(pune_officer),
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"
