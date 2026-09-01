import json

import pytest
from sqlalchemy.orm import Session

from app.agents.complaint_triage import agent as complaint_triage_agent
from app.repositories import complaint_category_repository
from app.services import ai_service
from app.tests.factories import (
    create_business,
    create_complaint,
    create_complaint_category,
    create_district,
    create_division,
    create_staff,
    create_user,
)
from app.utils.enums import ComplaintPriority, TriageStatus, UserRole
from app.utils.exceptions import (
    GeminiRateLimitedError,
    GeminiRequestError,
    GeminiUnavailableError,
    InvalidAiResponseError,
)

_CATEGORIES = [
    ("expired_food", "Expired Food"),
    ("spoiled_food", "Spoiled / Bad Food"),
    ("unhygienic_premises", "Unhygienic Conditions"),
    ("contamination", "Contamination"),
    ("improper_storage", "Storage Issues"),
    ("other", "Other"),
]


def _setup(db_session: Session):
    division = create_division(db_session, name="Pune Division", code="PUN")
    district = create_district(db_session, division, name="Pune", code="PUN")
    _, officer = create_staff(
        db_session, district, role=UserRole.DISTRICT_OFFICER, email="officer@example.com", employee_code="DO-PUN"
    )
    for key, name in _CATEGORIES:
        create_complaint_category(db_session, key=key, name=name)

    citizen = create_user(db_session, email="citizen@example.com", full_name="Asha Citizen")
    business = create_business(db_session, district, business_name="Shree Dairy")
    expired_category = complaint_category_repository.get_by_key(db_session, "expired_food")
    complaint = create_complaint(
        db_session,
        citizen,
        district,
        expired_category,
        business=business,
        title="Expired milk on sale",
        description="Found expired milk packets still being sold at the counter.",
    )
    return officer, complaint


def _valid_payload(**overrides) -> str:
    payload = {
        "category": "spoiled_food",
        "summary": "Citizen reports expired milk on sale.",
        "priority_suggestion": "high",
        "business_name": "Shree Dairy",
        "product": "milk",
        "missing_information": ["purchase date"],
        "confidence": 0.82,
    }
    payload.update(overrides)
    return json.dumps(payload)


def test_valid_response_maps_to_known_category(db_session: Session, monkeypatch) -> None:
    officer, complaint = _setup(db_session)
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: _valid_payload())

    triage = complaint_triage_agent.run_triage(db_session, officer, complaint)

    assert triage.status == TriageStatus.COMPLETED
    assert triage.suggested_category_raw == "spoiled_food"
    assert triage.suggested_category.key == "spoiled_food"
    assert triage.category_match_uncertain is False
    assert triage.suggested_priority == ComplaintPriority.HIGH
    assert triage.confidence == pytest.approx(0.82)
    assert triage.is_uncertain is False
    assert triage.entities == {"business_name": "Shree Dairy", "product": "milk"}
    assert triage.missing_information == ["purchase date"]
    assert triage.model_used


def test_unsupported_category_falls_back_to_other_and_marks_uncertain(db_session: Session, monkeypatch) -> None:
    officer, complaint = _setup(db_session)
    monkeypatch.setattr(
        ai_service, "generate_structured_json", lambda *a, **k: _valid_payload(category="pest_infestation")
    )

    triage = complaint_triage_agent.run_triage(db_session, officer, complaint)

    assert triage.status == TriageStatus.COMPLETED
    assert triage.suggested_category_raw == "pest_infestation"
    assert triage.category_match_uncertain is True
    assert triage.suggested_category is not None
    assert triage.suggested_category.key == "other"
    assert triage.is_uncertain is True


def test_category_synonym_maps_without_uncertainty(db_session: Session, monkeypatch) -> None:
    officer, complaint = _setup(db_session)
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: _valid_payload(category="Expired"))

    triage = complaint_triage_agent.run_triage(db_session, officer, complaint)

    assert triage.suggested_category.key == "expired_food"
    assert triage.category_match_uncertain is False


def test_unsupported_priority_defaults_to_medium_and_marks_uncertain(db_session: Session, monkeypatch) -> None:
    officer, complaint = _setup(db_session)
    monkeypatch.setattr(
        ai_service, "generate_structured_json", lambda *a, **k: _valid_payload(priority_suggestion="urgent")
    )

    triage = complaint_triage_agent.run_triage(db_session, officer, complaint)

    assert triage.suggested_priority == ComplaintPriority.MEDIUM
    assert triage.is_uncertain is True


def test_low_confidence_marks_uncertain_even_with_clean_mapping(db_session: Session, monkeypatch) -> None:
    officer, complaint = _setup(db_session)
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: _valid_payload(confidence=0.2))

    triage = complaint_triage_agent.run_triage(db_session, officer, complaint)

    assert triage.category_match_uncertain is False
    assert triage.is_uncertain is True


def test_malformed_json_persists_failed_status_and_raises(db_session: Session, monkeypatch) -> None:
    officer, complaint = _setup(db_session)
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: "not json")

    with pytest.raises(InvalidAiResponseError):
        complaint_triage_agent.run_triage(db_session, officer, complaint)

    latest = complaint_triage_agent.get_latest_triage(db_session, complaint.id)
    assert latest is not None
    assert latest.status == TriageStatus.FAILED
    assert latest.error_code == "INVALID_AI_RESPONSE"


def test_missing_required_field_persists_failed_status_and_raises(db_session: Session, monkeypatch) -> None:
    officer, complaint = _setup(db_session)
    incomplete = json.dumps({"category": "spoiled_food"})
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: incomplete)

    with pytest.raises(InvalidAiResponseError):
        complaint_triage_agent.run_triage(db_session, officer, complaint)

    latest = complaint_triage_agent.get_latest_triage(db_session, complaint.id)
    assert latest.status == TriageStatus.FAILED


def test_confidence_out_of_range_is_treated_as_malformed(db_session: Session, monkeypatch) -> None:
    officer, complaint = _setup(db_session)
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: _valid_payload(confidence=1.5))

    with pytest.raises(InvalidAiResponseError):
        complaint_triage_agent.run_triage(db_session, officer, complaint)


def test_non_retryable_gemini_error_fails_immediately_without_retry(db_session: Session, monkeypatch) -> None:
    officer, complaint = _setup(db_session)
    calls = []

    def _raise(*a, **k):
        calls.append(1)
        raise GeminiRequestError("bad request")

    monkeypatch.setattr(ai_service, "generate_structured_json", _raise)

    with pytest.raises(GeminiRequestError):
        complaint_triage_agent.run_triage(db_session, officer, complaint)

    assert len(calls) == 1
    latest = complaint_triage_agent.get_latest_triage(db_session, complaint.id)
    assert latest.status == TriageStatus.FAILED
    assert latest.error_code == "GEMINI_REQUEST_FAILED"


def test_rate_limited_error_retries_then_succeeds(db_session: Session, monkeypatch) -> None:
    officer, complaint = _setup(db_session)
    monkeypatch.setattr(complaint_triage_agent.time, "sleep", lambda *a, **k: None)
    calls = {"count": 0}

    def _flaky(*a, **k):
        calls["count"] += 1
        if calls["count"] == 1:
            raise GeminiRateLimitedError()
        return _valid_payload()

    monkeypatch.setattr(ai_service, "generate_structured_json", _flaky)

    triage = complaint_triage_agent.run_triage(db_session, officer, complaint)

    assert calls["count"] == 2
    assert triage.status == TriageStatus.COMPLETED


def test_server_error_retries_then_fails_after_max_attempts(db_session: Session, monkeypatch) -> None:
    officer, complaint = _setup(db_session)
    monkeypatch.setattr(complaint_triage_agent.time, "sleep", lambda *a, **k: None)
    calls = {"count": 0}

    def _always_fail(*a, **k):
        calls["count"] += 1
        raise GeminiUnavailableError()

    monkeypatch.setattr(ai_service, "generate_structured_json", _always_fail)

    with pytest.raises(GeminiUnavailableError):
        complaint_triage_agent.run_triage(db_session, officer, complaint)

    assert calls["count"] == complaint_triage_agent._MAX_ATTEMPTS
    latest = complaint_triage_agent.get_latest_triage(db_session, complaint.id)
    assert latest.status == TriageStatus.FAILED
    assert latest.error_code == "GEMINI_UNAVAILABLE"


def test_original_complaint_description_untouched_after_triage(db_session: Session, monkeypatch) -> None:
    officer, complaint = _setup(db_session)
    original_description = complaint.description
    original_priority = complaint.priority
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: _valid_payload())

    complaint_triage_agent.run_triage(db_session, officer, complaint)

    db_session.refresh(complaint)
    assert complaint.description == original_description
    assert complaint.priority == original_priority


def test_get_latest_triage_does_not_call_gemini(db_session: Session, monkeypatch) -> None:
    officer, complaint = _setup(db_session)

    def _fail_if_called(*a, **k):
        raise AssertionError("Gemini should not be called for a read-only fetch")

    monkeypatch.setattr(ai_service, "generate_structured_json", _fail_if_called)

    result = complaint_triage_agent.get_latest_triage(db_session, complaint.id)

    assert result is None


def test_get_latest_triage_returns_most_recent_run(db_session: Session, monkeypatch) -> None:
    officer, complaint = _setup(db_session)
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: _valid_payload(summary="First run"))
    complaint_triage_agent.run_triage(db_session, officer, complaint)

    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: _valid_payload(summary="Second run"))
    complaint_triage_agent.run_triage(db_session, officer, complaint)

    latest = complaint_triage_agent.get_latest_triage(db_session, complaint.id)
    assert latest.summary == "Second run"
