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
    create_inspection,
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

    pune_officer, officer_staff = create_staff(
        db_session, pune, role=UserRole.DISTRICT_OFFICER, email="pune.officer@example.com", employee_code="DO-PUN"
    )
    pune_inspector, inspector_staff = create_staff(
        db_session, pune, role=UserRole.INSPECTOR, email="pune.inspector@example.com", employee_code="INS-PUN"
    )
    other_inspector, other_inspector_staff = create_staff(
        db_session, pune, role=UserRole.INSPECTOR, email="other.inspector@example.com", employee_code="INS-PUN-2"
    )

    category = create_complaint_category(db_session, key="expired_food", name="Expired Food")
    citizen = create_user(db_session, email="citizen@example.com", full_name="Asha Citizen")
    business = create_business(db_session, pune, business_name="Shree Dairy")
    complaint = create_complaint(
        db_session, citizen, pune, category, business=business, complaint_number="MH-PUN-2026-000001"
    )
    # A separate complaint for the other inspector's inspection - `inspections`
    # has a unique constraint on complaint_id, so two inspections can't share one.
    other_complaint = create_complaint(
        db_session, citizen, pune, category, business=business, complaint_number="MH-PUN-2026-000002"
    )

    inspection = create_inspection(db_session, complaint, inspector_staff)
    other_inspection = create_inspection(db_session, other_complaint, other_inspector_staff)
    evidence = create_evidence(db_session, complaint, citizen, inspection_id=inspection.id)

    return pune_officer, pune_inspector, other_inspector, inspection, other_inspection, evidence


def _patch_bytes(monkeypatch) -> None:
    monkeypatch.setattr(evidence_service, "get_evidence_bytes", lambda evidence: _FAKE_IMAGE_BYTES)


def test_inspector_can_run_analysis_for_own_inspection_evidence(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _officer, inspector, _other, inspection, _other_inspection, evidence = _setup(db_session)
    _patch_bytes(monkeypatch)
    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", lambda *a, **k: _valid_payload())

    response = client.post(
        f"/api/v1/inspector/inspections/{inspection.id}/evidence/{evidence.id}/analysis",
        headers=auth_headers(inspector),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["product_name"] == "Toned Milk"


def test_inspector_cannot_analyze_evidence_from_another_inspectors_inspection(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _officer, _inspector, other_inspector, _inspection, other_inspection, evidence = _setup(db_session)
    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", lambda *a, **k: _valid_payload())

    response = client.post(
        f"/api/v1/inspector/inspections/{other_inspection.id}/evidence/{evidence.id}/analysis",
        headers=auth_headers(other_inspector),
    )

    assert response.status_code == 404


def test_get_analysis_returns_404_before_any_run(client: TestClient, db_session: Session) -> None:
    _officer, inspector, _other, inspection, _other_inspection, evidence = _setup(db_session)

    response = client.get(
        f"/api/v1/inspector/inspections/{inspection.id}/evidence/{evidence.id}/analysis",
        headers=auth_headers(inspector),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "EVIDENCE_ANALYSIS_NOT_FOUND"


def test_get_analysis_does_not_call_gemini_again(client: TestClient, db_session: Session, monkeypatch) -> None:
    _officer, inspector, _other, inspection, _other_inspection, evidence = _setup(db_session)
    _patch_bytes(monkeypatch)
    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", lambda *a, **k: _valid_payload())

    client.post(
        f"/api/v1/inspector/inspections/{inspection.id}/evidence/{evidence.id}/analysis",
        headers=auth_headers(inspector),
    )

    def _fail_if_called(*a, **k):
        raise AssertionError("GET should not call Gemini")

    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", _fail_if_called)

    response = client.get(
        f"/api/v1/inspector/inspections/{inspection.id}/evidence/{evidence.id}/analysis",
        headers=auth_headers(inspector),
    )

    assert response.status_code == 200


def test_officer_cannot_run_inspector_evidence_analysis_endpoint(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    officer, _inspector, _other, inspection, _other_inspection, evidence = _setup(db_session)
    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", lambda *a, **k: _valid_payload())

    response = client.post(
        f"/api/v1/inspector/inspections/{inspection.id}/evidence/{evidence.id}/analysis",
        headers=auth_headers(officer),
    )

    assert response.status_code == 403


def test_unauthenticated_request_is_rejected(client: TestClient, db_session: Session) -> None:
    _officer, _inspector, _other, inspection, _other_inspection, evidence = _setup(db_session)

    response = client.post(f"/api/v1/inspector/inspections/{inspection.id}/evidence/{evidence.id}/analysis")

    assert response.status_code == 401


def test_gemini_failure_returns_service_unavailable_and_persists_failure(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _officer, inspector, _other, inspection, _other_inspection, evidence = _setup(db_session)
    _patch_bytes(monkeypatch)

    def _raise(*a, **k):
        raise GeminiUnavailableError()

    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", _raise)
    monkeypatch.setattr(evidence_analysis_agent.time, "sleep", lambda *a, **k: None)

    response = client.post(
        f"/api/v1/inspector/inspections/{inspection.id}/evidence/{evidence.id}/analysis",
        headers=auth_headers(inspector),
    )

    assert response.status_code == 503

    get_response = client.get(
        f"/api/v1/inspector/inspections/{inspection.id}/evidence/{evidence.id}/analysis",
        headers=auth_headers(inspector),
    )
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "failed"
