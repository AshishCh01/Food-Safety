import json

import pytest
from sqlalchemy.orm import Session

from app.agents.evidence_analysis import agent as evidence_analysis_agent
from app.services import ai_service, evidence_service
from app.tests.factories import (
    create_business,
    create_complaint,
    create_complaint_category,
    create_district,
    create_division,
    create_evidence,
    create_staff,
    create_user,
)
from app.utils.enums import EvidenceAnalysisStatus, UserRole
from app.utils.exceptions import (
    GeminiRateLimitedError,
    GeminiRequestError,
    GeminiUnavailableError,
    InvalidAiResponseError,
)

_FAKE_IMAGE_BYTES = b"\xff\xd8\xff\xe0fake-jpeg-bytes"


def _setup(db_session: Session, *, file_type: str = "image/jpeg"):
    division = create_division(db_session, name="Pune Division", code="PUN")
    district = create_district(db_session, division, name="Pune", code="PUN")
    _, officer = create_staff(
        db_session, district, role=UserRole.DISTRICT_OFFICER, email="officer@example.com", employee_code="DO-PUN"
    )
    create_complaint_category(db_session, key="expired_food", name="Expired Food")

    citizen = create_user(db_session, email="citizen@example.com", full_name="Asha Citizen")
    business = create_business(db_session, district, business_name="Shree Dairy")
    category = create_complaint_category(db_session, key="other", name="Other")
    complaint = create_complaint(
        db_session,
        citizen,
        district,
        category,
        business=business,
        title="Expired milk on sale",
        description="Found expired milk packets still being sold at the counter.",
    )
    evidence = create_evidence(db_session, complaint, citizen, file_type=file_type)
    return officer, evidence


def _valid_payload(**overrides) -> str:
    payload = {
        "extracted_text": "Shree Dairy Toned Milk MFG 01/2026 EXP 01/2027",
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


def _patch_bytes(monkeypatch) -> None:
    monkeypatch.setattr(evidence_service, "get_evidence_bytes", lambda evidence: _FAKE_IMAGE_BYTES)


def test_valid_response_persists_completed_analysis(db_session: Session, monkeypatch) -> None:
    officer, evidence = _setup(db_session)
    _patch_bytes(monkeypatch)
    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", lambda *a, **k: _valid_payload())

    analysis = evidence_analysis_agent.run_analysis(db_session, officer, evidence)

    assert analysis.status == EvidenceAnalysisStatus.COMPLETED
    assert analysis.extracted_text == "Shree Dairy Toned Milk MFG 01/2026 EXP 01/2027"
    assert analysis.product_name == "Toned Milk"
    assert analysis.manufacturer == "Shree Dairy"
    assert analysis.batch_lot_number == "B12345"
    assert analysis.confidence == pytest.approx(0.85)
    assert analysis.is_uncertain is False
    assert analysis.model_used


def test_pdf_evidence_analysis_succeeds(db_session: Session, monkeypatch) -> None:
    officer, evidence = _setup(db_session, file_type="application/pdf")
    _patch_bytes(monkeypatch)
    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", lambda *a, **k: _valid_payload())

    analysis = evidence_analysis_agent.run_analysis(db_session, officer, evidence)

    assert analysis.status == EvidenceAnalysisStatus.COMPLETED


def test_unsupported_file_type_persists_failure_without_calling_gemini(db_session: Session, monkeypatch) -> None:
    officer, evidence = _setup(db_session, file_type="video/mp4")

    def _fail_if_called(*a, **k):
        raise AssertionError("Gemini should not be called for an unsupported file type")

    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", _fail_if_called)

    with pytest.raises(Exception):
        evidence_analysis_agent.run_analysis(db_session, officer, evidence)

    latest = evidence_analysis_agent.get_latest_analysis(db_session, evidence.id)
    assert latest is not None
    assert latest.status == EvidenceAnalysisStatus.FAILED
    assert latest.error_code == "UNSUPPORTED_FILE_TYPE"


def test_malformed_json_persists_failed_status_and_raises(db_session: Session, monkeypatch) -> None:
    officer, evidence = _setup(db_session)
    _patch_bytes(monkeypatch)
    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", lambda *a, **k: "not json")

    with pytest.raises(InvalidAiResponseError):
        evidence_analysis_agent.run_analysis(db_session, officer, evidence)

    latest = evidence_analysis_agent.get_latest_analysis(db_session, evidence.id)
    assert latest.status == EvidenceAnalysisStatus.FAILED
    assert latest.error_code == "INVALID_AI_RESPONSE"


def test_missing_required_field_persists_failed_status_and_raises(db_session: Session, monkeypatch) -> None:
    officer, evidence = _setup(db_session)
    _patch_bytes(monkeypatch)
    incomplete = json.dumps({"product_name": "Toned Milk"})
    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", lambda *a, **k: incomplete)

    with pytest.raises(InvalidAiResponseError):
        evidence_analysis_agent.run_analysis(db_session, officer, evidence)

    latest = evidence_analysis_agent.get_latest_analysis(db_session, evidence.id)
    assert latest.status == EvidenceAnalysisStatus.FAILED


def test_confidence_out_of_range_is_treated_as_malformed(db_session: Session, monkeypatch) -> None:
    officer, evidence = _setup(db_session)
    _patch_bytes(monkeypatch)
    monkeypatch.setattr(
        ai_service, "generate_structured_json_with_media", lambda *a, **k: _valid_payload(confidence=1.5)
    )

    with pytest.raises(InvalidAiResponseError):
        evidence_analysis_agent.run_analysis(db_session, officer, evidence)


def test_non_retryable_gemini_error_fails_immediately_without_retry(db_session: Session, monkeypatch) -> None:
    officer, evidence = _setup(db_session)
    _patch_bytes(monkeypatch)
    calls = []

    def _raise(*a, **k):
        calls.append(1)
        raise GeminiRequestError("bad request")

    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", _raise)

    with pytest.raises(GeminiRequestError):
        evidence_analysis_agent.run_analysis(db_session, officer, evidence)

    assert len(calls) == 1
    latest = evidence_analysis_agent.get_latest_analysis(db_session, evidence.id)
    assert latest.status == EvidenceAnalysisStatus.FAILED
    assert latest.error_code == "GEMINI_REQUEST_FAILED"


def test_rate_limited_error_retries_then_succeeds(db_session: Session, monkeypatch) -> None:
    officer, evidence = _setup(db_session)
    _patch_bytes(monkeypatch)
    monkeypatch.setattr(evidence_analysis_agent.time, "sleep", lambda *a, **k: None)
    calls = {"count": 0}

    def _flaky(*a, **k):
        calls["count"] += 1
        if calls["count"] == 1:
            raise GeminiRateLimitedError()
        return _valid_payload()

    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", _flaky)

    analysis = evidence_analysis_agent.run_analysis(db_session, officer, evidence)

    assert calls["count"] == 2
    assert analysis.status == EvidenceAnalysisStatus.COMPLETED


def test_server_error_retries_then_fails_after_max_attempts(db_session: Session, monkeypatch) -> None:
    officer, evidence = _setup(db_session)
    _patch_bytes(monkeypatch)
    monkeypatch.setattr(evidence_analysis_agent.time, "sleep", lambda *a, **k: None)
    calls = {"count": 0}

    def _always_fail(*a, **k):
        calls["count"] += 1
        raise GeminiUnavailableError()

    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", _always_fail)

    with pytest.raises(GeminiUnavailableError):
        evidence_analysis_agent.run_analysis(db_session, officer, evidence)

    assert calls["count"] == evidence_analysis_agent._MAX_ATTEMPTS
    latest = evidence_analysis_agent.get_latest_analysis(db_session, evidence.id)
    assert latest.status == EvidenceAnalysisStatus.FAILED
    assert latest.error_code == "GEMINI_UNAVAILABLE"


def test_expiry_date_in_past_flags_possible_expired(db_session: Session, monkeypatch) -> None:
    officer, evidence = _setup(db_session)
    _patch_bytes(monkeypatch)
    monkeypatch.setattr(
        ai_service, "generate_structured_json_with_media", lambda *a, **k: _valid_payload(expiry_date_text="01/01/2020")
    )

    analysis = evidence_analysis_agent.run_analysis(db_session, officer, evidence)

    assert analysis.possible_expired is True


def test_expiry_date_not_yet_past_is_not_flagged(db_session: Session, monkeypatch) -> None:
    officer, evidence = _setup(db_session)
    _patch_bytes(monkeypatch)
    monkeypatch.setattr(
        ai_service, "generate_structured_json_with_media", lambda *a, **k: _valid_payload(expiry_date_text="01/01/2099")
    )

    analysis = evidence_analysis_agent.run_analysis(db_session, officer, evidence)

    assert analysis.possible_expired is False


def test_unparseable_expiry_date_leaves_possible_expired_none_and_adds_uncertainty(
    db_session: Session, monkeypatch
) -> None:
    officer, evidence = _setup(db_session)
    _patch_bytes(monkeypatch)
    monkeypatch.setattr(
        ai_service,
        "generate_structured_json_with_media",
        lambda *a, **k: _valid_payload(expiry_date_text="best before summer"),
    )

    analysis = evidence_analysis_agent.run_analysis(db_session, officer, evidence)

    assert analysis.possible_expired is None
    assert "expiry date could not be reliably parsed" in (analysis.uncertainty_notes or [])
    assert analysis.is_uncertain is True


def test_no_expiry_date_extracted_leaves_possible_expired_none(db_session: Session, monkeypatch) -> None:
    officer, evidence = _setup(db_session)
    _patch_bytes(monkeypatch)
    monkeypatch.setattr(
        ai_service, "generate_structured_json_with_media", lambda *a, **k: _valid_payload(expiry_date_text=None)
    )

    analysis = evidence_analysis_agent.run_analysis(db_session, officer, evidence)

    assert analysis.possible_expired is None
    assert analysis.uncertainty_notes in (None, [])


def test_original_evidence_untouched_after_analysis(db_session: Session, monkeypatch) -> None:
    officer, evidence = _setup(db_session)
    _patch_bytes(monkeypatch)
    original_storage_path = evidence.storage_path
    original_file_type = evidence.file_type
    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", lambda *a, **k: _valid_payload())

    evidence_analysis_agent.run_analysis(db_session, officer, evidence)

    db_session.refresh(evidence)
    assert evidence.storage_path == original_storage_path
    assert evidence.file_type == original_file_type


def test_cached_completed_result_short_circuits_gemini_when_not_forced(db_session: Session, monkeypatch) -> None:
    officer, evidence = _setup(db_session)
    _patch_bytes(monkeypatch)
    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", lambda *a, **k: _valid_payload())
    first = evidence_analysis_agent.run_analysis(db_session, officer, evidence)

    def _fail_if_called(*a, **k):
        raise AssertionError("Gemini should not be called when a cached result exists")

    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", _fail_if_called)

    second = evidence_analysis_agent.run_analysis(db_session, officer, evidence, force=False)

    assert second.id == first.id


def test_force_reruns_even_with_cached_completed_result(db_session: Session, monkeypatch) -> None:
    officer, evidence = _setup(db_session)
    _patch_bytes(monkeypatch)
    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", lambda *a, **k: _valid_payload())
    first = evidence_analysis_agent.run_analysis(db_session, officer, evidence)

    calls = {"count": 0}

    def _rerun(*a, **k):
        calls["count"] += 1
        return _valid_payload(product_name="Re-analyzed Milk")

    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", _rerun)

    second = evidence_analysis_agent.run_analysis(db_session, officer, evidence, force=True)

    assert calls["count"] == 1
    assert second.id != first.id
    assert second.product_name == "Re-analyzed Milk"


def test_get_latest_analysis_does_not_call_gemini(db_session: Session, monkeypatch) -> None:
    _officer, evidence = _setup(db_session)

    def _fail_if_called(*a, **k):
        raise AssertionError("Gemini should not be called for a read-only fetch")

    monkeypatch.setattr(ai_service, "generate_structured_json_with_media", _fail_if_called)

    result = evidence_analysis_agent.get_latest_analysis(db_session, evidence.id)

    assert result is None


def test_get_latest_analysis_returns_most_recent_run(db_session: Session, monkeypatch) -> None:
    officer, evidence = _setup(db_session)
    _patch_bytes(monkeypatch)
    monkeypatch.setattr(
        ai_service, "generate_structured_json_with_media", lambda *a, **k: _valid_payload(product_name="First run")
    )
    evidence_analysis_agent.run_analysis(db_session, officer, evidence)

    monkeypatch.setattr(
        ai_service, "generate_structured_json_with_media", lambda *a, **k: _valid_payload(product_name="Second run")
    )
    evidence_analysis_agent.run_analysis(db_session, officer, evidence, force=True)

    latest = evidence_analysis_agent.get_latest_analysis(db_session, evidence.id)
    assert latest.product_name == "Second run"
