import json

import pytest
from sqlalchemy.orm import Session

from app.agents.investigation import agent as investigation_agent
from app.agents.investigation import tools as investigation_tools
from app.rag.retrieval import RetrievedChunk
from app.services import ai_service
from app.tests.factories import (
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
from app.utils.enums import ComplaintStatus, InspectionStatus, InvestigationStatus, UserRole
from app.utils.exceptions import (
    GeminiRateLimitedError,
    GeminiRequestError,
    GeminiUnavailableError,
    InvalidAiResponseError,
)


def _setup(db_session: Session, *, with_business: bool = True):
    division = create_division(db_session, name="Pune Division", code="PUN")
    district = create_district(db_session, division, name="Pune", code="PUN")
    _, officer = create_staff(
        db_session, district, role=UserRole.DISTRICT_OFFICER, email="officer@example.com", employee_code="DO-PUN"
    )
    category = create_complaint_category(db_session, key="expired_food", name="Expired Food")
    citizen = create_user(db_session, email="citizen@example.com", full_name="Asha Citizen")
    business = create_business(db_session, district, business_name="Shree Dairy") if with_business else None
    complaint = create_complaint(
        db_session,
        citizen,
        district,
        category,
        business=business,
        title="Expired milk on sale",
        description="Found expired milk packets still being sold at the counter.",
    )
    return district, officer, citizen, business, complaint


def _valid_payload(**overrides) -> str:
    payload = {
        "case_summary": "Citizen reports expired milk being sold at Shree Dairy.",
        "complaint_patterns": [],
        "risk_indicators": [],
        "missing_information": [],
        "suggested_actions": ["Verify current license status."],
        "regulatory_guidance": [],
        "confidence": 0.8,
        "is_uncertain": False,
        "uncertainty_reasons": [],
    }
    payload.update(overrides)
    return json.dumps(payload)


def _chunk(**overrides) -> RetrievedChunk:
    defaults = dict(
        chunk_id="c1",
        document_id="d1",
        document_title="FSSAI Food Safety and Standards Regulations",
        source_organization="FSSAI",
        document_type="regulation",
        page_number=42,
        section_title="Sale of expired products",
        content="No person shall sell any food product beyond its expiry date.",
        score=0.9,
    )
    defaults.update(overrides)
    return RetrievedChunk(**defaults)


def _no_chunks(monkeypatch) -> None:
    monkeypatch.setattr(investigation_agent.tools, "search_regulations", lambda *a, **k: [])


def test_valid_response_persists_completed_brief_with_resolved_citation(db_session: Session, monkeypatch) -> None:
    _district, officer, _citizen, _business, complaint = _setup(db_session)
    monkeypatch.setattr(investigation_agent.tools, "search_regulations", lambda *a, **k: [_chunk()])
    monkeypatch.setattr(
        ai_service,
        "generate_structured_json",
        lambda *a, **k: _valid_payload(
            regulatory_guidance=[{"guidance": "Expired products may not be sold.", "source_id": "R1"}]
        ),
    )

    brief = investigation_agent.run_investigation(db_session, officer, complaint)

    assert brief.status == InvestigationStatus.COMPLETED
    assert brief.case_summary == "Citizen reports expired milk being sold at Shree Dairy."
    assert brief.regulatory_guidance == [
        {
            "guidance": "Expired products may not be sold.",
            "citation": {
                "document_id": "d1",
                "title": "FSSAI Food Safety and Standards Regulations",
                "source_organization": "FSSAI",
                "page_number": 42,
                "section_title": "Sale of expired products",
            },
        }
    ]
    assert brief.is_uncertain is False
    assert brief.model_used


def test_hallucinated_source_id_is_dropped_and_forces_uncertain(db_session: Session, monkeypatch) -> None:
    _district, officer, _citizen, _business, complaint = _setup(db_session)
    monkeypatch.setattr(investigation_agent.tools, "search_regulations", lambda *a, **k: [_chunk()])
    monkeypatch.setattr(
        ai_service,
        "generate_structured_json",
        lambda *a, **k: _valid_payload(
            regulatory_guidance=[{"guidance": "Invented rule.", "source_id": "R99"}]
        ),
    )

    brief = investigation_agent.run_investigation(db_session, officer, complaint)

    assert brief.regulatory_guidance is None
    assert brief.is_uncertain is True
    assert any("could not be verified" in reason for reason in brief.uncertainty_reasons)


def test_no_regulatory_sources_found_forces_uncertain_without_fabricating(db_session: Session, monkeypatch) -> None:
    _district, officer, _citizen, _business, complaint = _setup(db_session)
    _no_chunks(monkeypatch)
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: _valid_payload())

    brief = investigation_agent.run_investigation(db_session, officer, complaint)

    assert brief.regulatory_guidance is None
    assert brief.is_uncertain is True
    assert any("No matching authoritative" in reason for reason in brief.uncertainty_reasons)


def test_deterministic_missing_information_detected_without_model_input(db_session: Session, monkeypatch) -> None:
    _district, officer, _citizen, business, complaint = _setup(db_session, with_business=False)
    assert business is None
    _no_chunks(monkeypatch)
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: _valid_payload())

    brief = investigation_agent.run_investigation(db_session, officer, complaint)

    assert "No business record is linked to this complaint." in brief.missing_information
    assert "No AI complaint triage has been completed for this complaint." in brief.missing_information
    assert "No completed AI evidence analysis is available for this complaint." in brief.missing_information
    assert "No inspection has been recorded for this complaint yet." in brief.missing_information


def test_relevant_evidence_and_business_history_are_tool_fetched_not_model_generated(
    db_session: Session, monkeypatch
) -> None:
    """These fields must reflect controlled tool output exactly, regardless
    of anything the model returns - the model has no field for them at all."""
    _district, officer, citizen, business, complaint = _setup(db_session)
    create_evidence(db_session, complaint, citizen, file_name="label.jpg")
    _no_chunks(monkeypatch)
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: _valid_payload())

    def _fake_evidence_analysis(db, complaint_arg):
        return [{"evidence_id": "fixed", "file_name": "label.jpg", "product_name": "Toned Milk"}]

    monkeypatch.setattr(investigation_agent.tools, "get_evidence_analysis", _fake_evidence_analysis)

    brief = investigation_agent.run_investigation(db_session, officer, complaint)

    assert brief.relevant_evidence == [{"evidence_id": "fixed", "file_name": "label.jpg", "product_name": "Toned Milk"}]
    assert brief.business_history["business"]["business_name"] == "Shree Dairy"
    assert brief.business_history["previous_complaints_count"] == 0


def test_malformed_json_persists_failed_status_and_raises(db_session: Session, monkeypatch) -> None:
    _district, officer, _citizen, _business, complaint = _setup(db_session)
    _no_chunks(monkeypatch)
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: "not json")

    with pytest.raises(InvalidAiResponseError):
        investigation_agent.run_investigation(db_session, officer, complaint)

    latest = investigation_agent.get_latest_investigation(db_session, complaint.id)
    assert latest.status == InvestigationStatus.FAILED
    assert latest.error_code == "INVALID_AI_RESPONSE"


def test_non_retryable_gemini_error_fails_immediately_without_retry(db_session: Session, monkeypatch) -> None:
    _district, officer, _citizen, _business, complaint = _setup(db_session)
    _no_chunks(monkeypatch)
    calls = []

    def _raise(*a, **k):
        calls.append(1)
        raise GeminiRequestError("bad request")

    monkeypatch.setattr(ai_service, "generate_structured_json", _raise)

    with pytest.raises(GeminiRequestError):
        investigation_agent.run_investigation(db_session, officer, complaint)

    assert len(calls) == 1
    latest = investigation_agent.get_latest_investigation(db_session, complaint.id)
    assert latest.status == InvestigationStatus.FAILED
    assert latest.error_code == "GEMINI_REQUEST_FAILED"


def test_rate_limited_error_retries_then_succeeds(db_session: Session, monkeypatch) -> None:
    _district, officer, _citizen, _business, complaint = _setup(db_session)
    _no_chunks(monkeypatch)
    monkeypatch.setattr(investigation_agent.time, "sleep", lambda *a, **k: None)
    calls = {"count": 0}

    def _flaky(*a, **k):
        calls["count"] += 1
        if calls["count"] == 1:
            raise GeminiRateLimitedError()
        return _valid_payload()

    monkeypatch.setattr(ai_service, "generate_structured_json", _flaky)

    brief = investigation_agent.run_investigation(db_session, officer, complaint)

    assert calls["count"] == 2
    assert brief.status == InvestigationStatus.COMPLETED


def test_server_error_retries_then_fails_after_max_attempts(db_session: Session, monkeypatch) -> None:
    _district, officer, _citizen, _business, complaint = _setup(db_session)
    _no_chunks(monkeypatch)
    monkeypatch.setattr(investigation_agent.time, "sleep", lambda *a, **k: None)
    calls = {"count": 0}

    def _always_fail(*a, **k):
        calls["count"] += 1
        raise GeminiUnavailableError()

    monkeypatch.setattr(ai_service, "generate_structured_json", _always_fail)

    with pytest.raises(GeminiUnavailableError):
        investigation_agent.run_investigation(db_session, officer, complaint)

    assert calls["count"] == investigation_agent._MAX_ATTEMPTS
    latest = investigation_agent.get_latest_investigation(db_session, complaint.id)
    assert latest.status == InvestigationStatus.FAILED


def test_cached_completed_result_short_circuits_gemini_when_not_forced(db_session: Session, monkeypatch) -> None:
    _district, officer, _citizen, _business, complaint = _setup(db_session)
    _no_chunks(monkeypatch)
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: _valid_payload())
    first = investigation_agent.run_investigation(db_session, officer, complaint)

    def _fail_if_called(*a, **k):
        raise AssertionError("Gemini should not be called when a cached result exists")

    monkeypatch.setattr(ai_service, "generate_structured_json", _fail_if_called)

    second = investigation_agent.run_investigation(db_session, officer, complaint, force=False)

    assert second.id == first.id


def test_force_reruns_even_with_cached_completed_result(db_session: Session, monkeypatch) -> None:
    _district, officer, _citizen, _business, complaint = _setup(db_session)
    _no_chunks(monkeypatch)
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: _valid_payload())
    first = investigation_agent.run_investigation(db_session, officer, complaint)

    calls = {"count": 0}

    def _rerun(*a, **k):
        calls["count"] += 1
        return _valid_payload(case_summary="Updated summary after re-investigation.")

    monkeypatch.setattr(ai_service, "generate_structured_json", _rerun)

    second = investigation_agent.run_investigation(db_session, officer, complaint, force=True)

    assert calls["count"] == 1
    assert second.id != first.id
    assert second.case_summary == "Updated summary after re-investigation."


def test_get_latest_investigation_does_not_call_gemini(db_session: Session, monkeypatch) -> None:
    _district, _officer, _citizen, _business, complaint = _setup(db_session)

    def _fail_if_called(*a, **k):
        raise AssertionError("Gemini should not be called for a read-only fetch")

    monkeypatch.setattr(ai_service, "generate_structured_json", _fail_if_called)

    result = investigation_agent.get_latest_investigation(db_session, complaint.id)

    assert result is None


def test_original_complaint_and_inspection_untouched_after_investigation(db_session: Session, monkeypatch) -> None:
    """The agent must never mutate the source-of-truth complaint/inspection
    records or drive a status transition - docs/AI_AGENTS_ARCHITECTURE.md
    section 12."""
    _district, officer, _citizen, _business, complaint = _setup(db_session)
    inspection = create_inspection(db_session, complaint, officer, status=InspectionStatus.SCHEDULED)
    original_status = complaint.status
    original_description = complaint.description
    original_inspection_status = inspection.inspection_status
    _no_chunks(monkeypatch)
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: _valid_payload())

    investigation_agent.run_investigation(db_session, officer, complaint)

    db_session.refresh(complaint)
    db_session.refresh(inspection)
    assert complaint.status == original_status == ComplaintStatus.SUBMITTED
    assert complaint.description == original_description
    assert inspection.inspection_status == original_inspection_status


def test_investigation_brief_never_changes_complaint_status(db_session: Session, monkeypatch) -> None:
    """The final regulatory decision remains with the officer - running an
    investigation must never itself resolve/reject a complaint."""
    _district, officer, _citizen, _business, complaint = _setup(db_session)
    _no_chunks(monkeypatch)
    monkeypatch.setattr(
        ai_service,
        "generate_structured_json",
        lambda *a, **k: _valid_payload(risk_indicators=["High risk of repeat violation."]),
    )

    investigation_agent.run_investigation(db_session, officer, complaint)

    db_session.refresh(complaint)
    assert complaint.status == ComplaintStatus.SUBMITTED


def test_get_complaint_history_is_scoped_to_requesting_officers_district(db_session: Session) -> None:
    """docs/SECURITY_AND_RBAC.md section 4 - district isolation must be
    enforced in the tool itself, not left to the LLM."""
    division = create_division(db_session, name="Pune Division", code="PUN")
    pune = create_district(db_session, division, name="Pune", code="PUN")
    nagpur = create_district(db_session, division, name="Nagpur", code="NGP")
    _, pune_officer = create_staff(
        db_session, pune, role=UserRole.DISTRICT_OFFICER, email="pune.officer@example.com", employee_code="DO-PUN"
    )
    category = create_complaint_category(db_session, key="expired_food", name="Expired Food")
    citizen = create_user(db_session, email="citizen@example.com")
    business = create_business(db_session, pune, business_name="Shree Dairy")

    pune_complaint = create_complaint(db_session, citizen, pune, category, business=business)
    nagpur_complaint = create_complaint(db_session, citizen, nagpur, category, business=business)

    history = investigation_tools.get_complaint_history(db_session, business, pune_officer)

    complaint_ids = {entry["complaint_number"] for entry in history}
    assert pune_complaint.complaint_number in complaint_ids
    assert nagpur_complaint.complaint_number not in complaint_ids
