from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.agents.investigation import agent as investigation_agent
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
from app.utils.exceptions import GeminiUnavailableError, GroqUnavailableError


def _valid_payload() -> str:
    import json

    return json.dumps(
        {
            "case_summary": "Citizen reports expired milk on sale at Shree Dairy.",
            "complaint_patterns": [],
            "risk_indicators": [],
            "missing_information": [],
            "suggested_actions": ["Verify current license status before scheduling a visit."],
            "regulatory_guidance": [],
            "confidence": 0.75,
            "is_uncertain": False,
            "uncertainty_reasons": [],
        }
    )


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


def test_officer_can_run_investigation_for_own_district_complaint(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    pune_officer, _pune_inspector, pune_complaint, _nagpur_complaint = _setup(db_session)
    monkeypatch.setattr(investigation_agent.tools, "search_regulations", lambda *a, **k: [])
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: _valid_payload())

    response = client.post(
        f"/api/v1/officer/complaints/{pune_complaint.id}/investigation", headers=auth_headers(pune_officer)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["case_summary"] == "Citizen reports expired milk on sale at Shree Dairy."
    assert body["suggested_actions"] == ["Verify current license status before scheduling a visit."]
    assert body["business_history"]["business"]["business_name"] == "Shree Dairy"
    assert body["model_used"]


def test_officer_cannot_run_investigation_for_another_districts_complaint(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    pune_officer, _pune_inspector, _pune_complaint, nagpur_complaint = _setup(db_session)
    monkeypatch.setattr(investigation_agent.tools, "search_regulations", lambda *a, **k: [])
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: _valid_payload())

    response = client.post(
        f"/api/v1/officer/complaints/{nagpur_complaint.id}/investigation", headers=auth_headers(pune_officer)
    )

    assert response.status_code == 404


def test_inspector_cannot_run_investigation(client: TestClient, db_session: Session, monkeypatch) -> None:
    _pune_officer, pune_inspector, pune_complaint, _nagpur_complaint = _setup(db_session)
    monkeypatch.setattr(investigation_agent.tools, "search_regulations", lambda *a, **k: [])
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: _valid_payload())

    response = client.post(
        f"/api/v1/officer/complaints/{pune_complaint.id}/investigation", headers=auth_headers(pune_inspector)
    )

    assert response.status_code == 403


def test_unauthenticated_request_is_rejected(client: TestClient, db_session: Session) -> None:
    _pune_officer, _pune_inspector, pune_complaint, _nagpur_complaint = _setup(db_session)

    response = client.post(f"/api/v1/officer/complaints/{pune_complaint.id}/investigation")

    assert response.status_code == 401


def test_get_investigation_returns_404_before_any_run(client: TestClient, db_session: Session) -> None:
    pune_officer, _pune_inspector, pune_complaint, _nagpur_complaint = _setup(db_session)

    response = client.get(
        f"/api/v1/officer/complaints/{pune_complaint.id}/investigation", headers=auth_headers(pune_officer)
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "INVESTIGATION_NOT_FOUND"


def test_get_investigation_returns_cached_result_without_calling_gemini_again(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    pune_officer, _pune_inspector, pune_complaint, _nagpur_complaint = _setup(db_session)
    monkeypatch.setattr(investigation_agent.tools, "search_regulations", lambda *a, **k: [])
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: _valid_payload())

    post_response = client.post(
        f"/api/v1/officer/complaints/{pune_complaint.id}/investigation", headers=auth_headers(pune_officer)
    )
    assert post_response.status_code == 200

    def _fail_if_called(*a, **k):
        raise AssertionError("GET should not call Gemini again")

    monkeypatch.setattr(ai_service, "generate_structured_json", _fail_if_called)

    get_response = client.get(
        f"/api/v1/officer/complaints/{pune_complaint.id}/investigation", headers=auth_headers(pune_officer)
    )

    assert get_response.status_code == 200
    assert get_response.json()["case_summary"] == post_response.json()["case_summary"]


def test_re_running_without_force_reuses_cached_result(client: TestClient, db_session: Session, monkeypatch) -> None:
    pune_officer, _pune_inspector, pune_complaint, _nagpur_complaint = _setup(db_session)
    monkeypatch.setattr(investigation_agent.tools, "search_regulations", lambda *a, **k: [])
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: _valid_payload())

    first = client.post(
        f"/api/v1/officer/complaints/{pune_complaint.id}/investigation", headers=auth_headers(pune_officer)
    )
    assert first.status_code == 200

    def _fail_if_called(*a, **k):
        raise AssertionError("Re-running without force should not call Gemini again")

    monkeypatch.setattr(ai_service, "generate_structured_json", _fail_if_called)

    second = client.post(
        f"/api/v1/officer/complaints/{pune_complaint.id}/investigation", headers=auth_headers(pune_officer)
    )

    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]


def test_force_re_run_calls_gemini_again_and_creates_new_brief(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    pune_officer, _pune_inspector, pune_complaint, _nagpur_complaint = _setup(db_session)
    monkeypatch.setattr(investigation_agent.tools, "search_regulations", lambda *a, **k: [])
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: _valid_payload())

    first = client.post(
        f"/api/v1/officer/complaints/{pune_complaint.id}/investigation", headers=auth_headers(pune_officer)
    )
    assert first.status_code == 200

    calls = {"count": 0}

    def _rerun(*a, **k):
        calls["count"] += 1
        import json

        return json.dumps(
            {
                "case_summary": "Updated after re-investigation.",
                "complaint_patterns": [],
                "risk_indicators": [],
                "missing_information": [],
                "suggested_actions": [],
                "regulatory_guidance": [],
                "confidence": 0.9,
                "is_uncertain": False,
                "uncertainty_reasons": [],
            }
        )

    monkeypatch.setattr(ai_service, "generate_structured_json", _rerun)

    second = client.post(
        f"/api/v1/officer/complaints/{pune_complaint.id}/investigation?force=true", headers=auth_headers(pune_officer)
    )

    assert second.status_code == 200
    assert calls["count"] == 1
    assert second.json()["id"] != first.json()["id"]
    assert second.json()["case_summary"] == "Updated after re-investigation."


def test_gemini_failure_returns_service_unavailable_and_persists_failure(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    pune_officer, _pune_inspector, pune_complaint, _nagpur_complaint = _setup(db_session)
    monkeypatch.setattr(investigation_agent.tools, "search_regulations", lambda *a, **k: [])

    def _raise(*a, **k):
        raise GeminiUnavailableError()

    monkeypatch.setattr(ai_service, "generate_structured_json", _raise)
    monkeypatch.setattr(investigation_agent.time, "sleep", lambda *a, **k: None)
    # Gemini exhausting retries now falls through to the Groq fallback (see
    # app.agents.investigation.agent) - fail that too, so this test still
    # exercises (and asserts on) the final, no-provider-available outcome.
    monkeypatch.setattr(ai_service, "generate_structured_json_groq", lambda *a, **k: (_ for _ in ()).throw(GroqUnavailableError()))

    response = client.post(
        f"/api/v1/officer/complaints/{pune_complaint.id}/investigation", headers=auth_headers(pune_officer)
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "GROQ_UNAVAILABLE"

    get_response = client.get(
        f"/api/v1/officer/complaints/{pune_complaint.id}/investigation", headers=auth_headers(pune_officer)
    )
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "failed"
    assert get_response.json()["error_code"] == "GROQ_UNAVAILABLE"


def test_running_investigation_never_changes_complaint_status(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    """The Investigation Agent is advisory only - the final decision remains
    with the officer (docs/AI_AGENTS_ARCHITECTURE.md section 12)."""
    pune_officer, _pune_inspector, pune_complaint, _nagpur_complaint = _setup(db_session)
    monkeypatch.setattr(investigation_agent.tools, "search_regulations", lambda *a, **k: [])
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: _valid_payload())

    response = client.post(
        f"/api/v1/officer/complaints/{pune_complaint.id}/investigation", headers=auth_headers(pune_officer)
    )
    assert response.status_code == 200

    complaint_response = client.get(
        f"/api/v1/officer/complaints/{pune_complaint.id}", headers=auth_headers(pune_officer)
    )
    assert complaint_response.json()["status"] == "submitted"
