import json

import pytest
from sqlalchemy.orm import Session

from app.agents.inspector_assistant import agent as inspector_assistant_agent
from app.rag.retrieval import RetrievedChunk
from app.services import ai_service
from app.tests.factories import (
    create_assistant_conversation,
    create_business,
    create_complaint,
    create_complaint_category,
    create_district,
    create_division,
    create_inspection,
    create_staff,
    create_user,
)
from app.utils.enums import AssistantMessageRole, UserRole
from app.utils.exceptions import (
    GeminiRequestError,
    GeminiUnavailableError,
    GroqUnavailableError,
    InvalidAiResponseError,
)

_INTENT_NONE = {
    "needs_regulatory_search": False,
    "needs_inspection_guideline_search": False,
    "search_query": "",
    "needs_business_context": False,
    "needs_complaint_history": False,
    "needs_inspection_history": False,
    "needs_evidence_analysis": False,
}


def _intent(**overrides) -> str:
    payload = dict(_INTENT_NONE)
    payload.update(overrides)
    return json.dumps(payload)


def _answer(**overrides) -> str:
    payload = {"answer": "Here is the answer.", "used_source_ids": [], "is_uncertain": False, "uncertainty_reason": None}
    payload.update(overrides)
    return json.dumps(payload)


def _setup_general(db_session: Session):
    division = create_division(db_session, name="Pune Division", code="PUN")
    district = create_district(db_session, division, name="Pune", code="PUN")
    _, inspector_staff = create_staff(
        db_session, district, role=UserRole.INSPECTOR, email="inspector@example.com", employee_code="INS-PUN"
    )
    conversation = create_assistant_conversation(db_session, inspector_staff)
    return inspector_staff, conversation


def _setup_case(db_session: Session):
    division = create_division(db_session, name="Pune Division", code="PUN")
    district = create_district(db_session, division, name="Pune", code="PUN")

    _, inspector_staff = create_staff(
        db_session, district, role=UserRole.INSPECTOR, email="inspector@example.com", employee_code="INS-PUN"
    )
    category = create_complaint_category(db_session, key="expired_food", name="Expired Food")
    citizen = create_user(db_session, email="citizen@example.com")
    business = create_business(db_session, district, business_name="Shree Dairy")
    complaint = create_complaint(db_session, citizen, district, category, business=business)
    inspection = create_inspection(db_session, complaint, inspector_staff)
    conversation = create_assistant_conversation(db_session, inspector_staff, inspection=inspection)
    return inspector_staff, conversation


def _queue(monkeypatch, *responses):
    calls = {"i": 0}

    def _fake(prompt, response_schema):
        value = responses[calls["i"]]
        calls["i"] += 1
        return value

    monkeypatch.setattr(ai_service, "generate_structured_json", _fake)
    return calls


def test_general_question_with_no_case_context_answers_without_app_data(db_session: Session, monkeypatch) -> None:
    staff, conversation = _setup_general(db_session)
    _queue(monkeypatch, _intent(), _answer(answer="Hello, how can I help?"))

    message = inspector_assistant_agent.ask(db_session, staff, conversation, "Hi there")

    assert message.role == AssistantMessageRole.ASSISTANT
    assert message.content == "Hello, how can I help?"
    assert message.citations is None
    assert message.application_data_used is None
    assert message.error_code is None


def test_regulatory_search_attaches_citations_for_referenced_chunks(db_session: Session, monkeypatch) -> None:
    staff, conversation = _setup_general(db_session)
    chunk = RetrievedChunk(
        chunk_id="c1",
        document_id="d1",
        document_title="FSSAI Act 2006",
        source_organization="FSSAI",
        document_type="law",
        page_number=12,
        section_title="Hygiene",
        content="Food handlers must wash hands.",
        score=0.9,
    )
    monkeypatch.setattr(inspector_assistant_agent.tools, "search_regulations", lambda *a, **k: [chunk])
    _queue(
        monkeypatch,
        _intent(needs_regulatory_search=True, search_query="hand hygiene"),
        _answer(answer="Wash hands per FSSAI rules.", used_source_ids=["R1"]),
    )

    message = inspector_assistant_agent.ask(db_session, staff, conversation, "What are hand hygiene rules?")

    assert message.citations == [
        {
            "document_id": "d1",
            "title": "FSSAI Act 2006",
            "source_organization": "FSSAI",
            "page_number": 12,
            "section_title": "Hygiene",
        }
    ]


def test_hallucinated_source_id_is_dropped(db_session: Session, monkeypatch) -> None:
    staff, conversation = _setup_general(db_session)
    monkeypatch.setattr(inspector_assistant_agent.tools, "search_regulations", lambda *a, **k: [])
    _queue(
        monkeypatch,
        _intent(needs_regulatory_search=True, search_query="anything"),
        _answer(answer="Some answer.", used_source_ids=["R1", "R99"], is_uncertain=True),
    )

    message = inspector_assistant_agent.ask(db_session, staff, conversation, "Tell me about regulation X")

    assert message.citations is None


def test_empty_retrieval_forces_uncertain_and_does_not_fabricate(db_session: Session, monkeypatch) -> None:
    staff, conversation = _setup_general(db_session)
    monkeypatch.setattr(inspector_assistant_agent.tools, "search_regulations", lambda *a, **k: [])
    _queue(
        monkeypatch,
        _intent(needs_regulatory_search=True, search_query="obscure topic"),
        _answer(answer="I could not find relevant regulations.", used_source_ids=[], is_uncertain=False),
    )

    message = inspector_assistant_agent.ask(db_session, staff, conversation, "What does obscure law X say?")

    assert message.is_uncertain is True
    assert message.uncertainty_reason


def test_case_context_always_includes_current_complaint(db_session: Session, monkeypatch) -> None:
    staff, conversation = _setup_case(db_session)
    _queue(monkeypatch, _intent(), _answer(used_source_ids=["A1"]))

    message = inspector_assistant_agent.ask(db_session, staff, conversation, "Summarize this case")

    assert message.application_data_used is not None
    labels = [entry["label"] for entry in message.application_data_used]
    assert "Current complaint" in labels


def test_evidence_analysis_tool_only_runs_when_flagged(db_session: Session, monkeypatch) -> None:
    staff, conversation = _setup_case(db_session)
    called = {"count": 0}

    def _track(*a, **k):
        called["count"] += 1
        return []

    monkeypatch.setattr(inspector_assistant_agent.tools, "get_evidence_analysis", _track)
    _queue(monkeypatch, _intent(needs_evidence_analysis=False), _answer())

    inspector_assistant_agent.ask(db_session, staff, conversation, "Any updates?")

    assert called["count"] == 0

    _queue(monkeypatch, _intent(needs_evidence_analysis=True), _answer())
    inspector_assistant_agent.ask(db_session, staff, conversation, "What did the evidence analysis show?")

    assert called["count"] == 1


def test_general_conversation_never_calls_case_scoped_tools(db_session: Session, monkeypatch) -> None:
    staff, conversation = _setup_general(db_session)

    def _fail(*a, **k):
        raise AssertionError("case-scoped tool should not be called without case context")

    monkeypatch.setattr(inspector_assistant_agent.tools, "get_previous_complaints", _fail)
    monkeypatch.setattr(inspector_assistant_agent.tools, "get_inspection_history", _fail)
    monkeypatch.setattr(inspector_assistant_agent.tools, "get_evidence_analysis", _fail)
    _queue(
        monkeypatch,
        _intent(needs_business_context=True, needs_complaint_history=True, needs_inspection_history=True, needs_evidence_analysis=True),
        _answer(),
    )

    message = inspector_assistant_agent.ask(db_session, staff, conversation, "General question")

    assert message.application_data_used is None


def test_malformed_intent_json_raises_and_persists_failure(db_session: Session, monkeypatch) -> None:
    staff, conversation = _setup_general(db_session)
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: "not json")

    with pytest.raises(InvalidAiResponseError):
        inspector_assistant_agent.ask(db_session, staff, conversation, "Question")

    from app.repositories import assistant_repository

    messages = assistant_repository.list_messages(db_session, conversation.id)
    assert messages[-1].error_code == "INVALID_AI_RESPONSE"


def test_malformed_answer_json_raises_and_persists_failure(db_session: Session, monkeypatch) -> None:
    staff, conversation = _setup_general(db_session)
    _queue(monkeypatch, _intent(), "not json")

    with pytest.raises(InvalidAiResponseError):
        inspector_assistant_agent.ask(db_session, staff, conversation, "Question")

    from app.repositories import assistant_repository

    messages = assistant_repository.list_messages(db_session, conversation.id)
    assert messages[-1].error_code == "INVALID_AI_RESPONSE"


def test_gemini_failure_at_intent_stage_persists_failed_message_without_crash(
    db_session: Session, monkeypatch
) -> None:
    staff, conversation = _setup_general(db_session)

    def _raise(*a, **k):
        raise GeminiRequestError("bad request")

    monkeypatch.setattr(ai_service, "generate_structured_json", _raise)

    message = inspector_assistant_agent.ask(db_session, staff, conversation, "Question")

    assert message.error_code == "GEMINI_REQUEST_FAILED"
    assert message.role == AssistantMessageRole.ASSISTANT


def test_gemini_failure_at_answer_stage_persists_failed_message_without_crash(
    db_session: Session, monkeypatch
) -> None:
    staff, conversation = _setup_general(db_session)

    def _raise(*a, **k):
        raise GeminiUnavailableError()

    monkeypatch.setattr(ai_service, "generate_structured_json", _raise)
    monkeypatch.setattr(inspector_assistant_agent.time, "sleep", lambda *a, **k: None)
    # Gemini exhausting retries now falls through to the Groq fallback (see
    # app.agents.inspector_assistant.agent) - fail that too, so this test
    # still exercises (and asserts on) the final, no-provider-available
    # outcome.
    monkeypatch.setattr(ai_service, "generate_structured_json_groq", lambda *a, **k: (_ for _ in ()).throw(GroqUnavailableError()))

    message = inspector_assistant_agent.ask(db_session, staff, conversation, "Question")

    assert message.error_code == "GROQ_UNAVAILABLE"


def test_application_data_used_shown_even_if_model_ignores_it(db_session: Session, monkeypatch) -> None:
    """App-data blocks are server-fetched and never fabricated, so they are
    surfaced in full regardless of whether the model's used_source_ids
    mentions them - unlike RAG citations, which are filtered."""
    staff, conversation = _setup_case(db_session)
    _queue(monkeypatch, _intent(), _answer(used_source_ids=[]))

    message = inspector_assistant_agent.ask(db_session, staff, conversation, "Summarize this case")

    assert message.application_data_used is not None
    assert len(message.application_data_used) >= 1
