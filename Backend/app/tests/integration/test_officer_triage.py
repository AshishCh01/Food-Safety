import json

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.agents.complaint_triage import agent as complaint_triage_agent
from app.services import ai_service
from app.tests.factories import (
    auth_headers,
    create_business,
    create_complaint,
    create_complaint_category,
    create_district,
    create_division,
    create_staff,
    create_user,
)
from app.utils.enums import UserRole
from app.utils.exceptions import GeminiUnavailableError


def _valid_payload(**overrides) -> str:
    payload = {
        "category": "expired_food",
        "summary": "Citizen reports expired milk on sale.",
        "priority_suggestion": "high",
        "business_name": "Shree Dairy",
        "product": "milk",
        "missing_information": ["purchase date"],
        "confidence": 0.82,
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

    return pune_officer, pune_inspector, pune_complaint, nagpur_complaint


def test_officer_can_run_triage_for_own_district_complaint(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    pune_officer, _pune_inspector, pune_complaint, _nagpur_complaint = _setup(db_session)
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: _valid_payload())

    response = client.post(f"/api/v1/officer/complaints/{pune_complaint.id}/triage", headers=auth_headers(pune_officer))

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed"
    assert body["suggested_category_name"] == "Expired Food"
    assert body["category_match_uncertain"] is False
    assert body["suggested_priority"] == "high"
    assert body["entities"]["business_name"] == "Shree Dairy"
    assert body["entities"]["product"] == "milk"
    assert body["missing_information"] == ["purchase date"]
    assert body["is_uncertain"] is False
    assert body["model_used"]


def test_officer_cannot_run_triage_for_another_districts_complaint(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    pune_officer, _pune_inspector, _pune_complaint, nagpur_complaint = _setup(db_session)
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: _valid_payload())

    response = client.post(
        f"/api/v1/officer/complaints/{nagpur_complaint.id}/triage", headers=auth_headers(pune_officer)
    )

    assert response.status_code == 404


def test_get_triage_returns_404_before_any_run(client: TestClient, db_session: Session) -> None:
    pune_officer, _pune_inspector, pune_complaint, _nagpur_complaint = _setup(db_session)

    response = client.get(f"/api/v1/officer/complaints/{pune_complaint.id}/triage", headers=auth_headers(pune_officer))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TRIAGE_NOT_FOUND"


def test_get_triage_returns_cached_result_without_calling_gemini_again(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    pune_officer, _pune_inspector, pune_complaint, _nagpur_complaint = _setup(db_session)
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: _valid_payload())

    post_response = client.post(
        f"/api/v1/officer/complaints/{pune_complaint.id}/triage", headers=auth_headers(pune_officer)
    )
    assert post_response.status_code == 201

    def _fail_if_called(*a, **k):
        raise AssertionError("GET should not call Gemini again")

    monkeypatch.setattr(ai_service, "generate_structured_json", _fail_if_called)

    get_response = client.get(f"/api/v1/officer/complaints/{pune_complaint.id}/triage", headers=auth_headers(pune_officer))

    assert get_response.status_code == 200
    assert get_response.json()["summary"] == post_response.json()["summary"]


def test_inspector_cannot_run_triage(client: TestClient, db_session: Session, monkeypatch) -> None:
    pune_officer, pune_inspector, pune_complaint, _nagpur_complaint = _setup(db_session)
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: _valid_payload())

    response = client.post(f"/api/v1/officer/complaints/{pune_complaint.id}/triage", headers=auth_headers(pune_inspector))

    assert response.status_code == 403


def test_unauthenticated_request_is_rejected(client: TestClient, db_session: Session) -> None:
    _pune_officer, _pune_inspector, pune_complaint, _nagpur_complaint = _setup(db_session)

    response = client.post(f"/api/v1/officer/complaints/{pune_complaint.id}/triage")

    assert response.status_code == 401


def test_gemini_failure_returns_service_unavailable_and_persists_failure(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    pune_officer, _pune_inspector, pune_complaint, _nagpur_complaint = _setup(db_session)

    def _raise(*a, **k):
        raise GeminiUnavailableError()

    monkeypatch.setattr(ai_service, "generate_structured_json", _raise)
    monkeypatch.setattr(complaint_triage_agent.time, "sleep", lambda *a, **k: None)

    response = client.post(f"/api/v1/officer/complaints/{pune_complaint.id}/triage", headers=auth_headers(pune_officer))

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "GEMINI_UNAVAILABLE"

    get_response = client.get(f"/api/v1/officer/complaints/{pune_complaint.id}/triage", headers=auth_headers(pune_officer))
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "failed"
    assert get_response.json()["error_code"] == "GEMINI_UNAVAILABLE"
