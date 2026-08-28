import json

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services import ai_service
from app.tests.factories import (
    auth_headers,
    create_business,
    create_complaint,
    create_complaint_category,
    create_district,
    create_division,
    create_inspection,
    create_staff,
    create_user,
)
from app.utils.enums import UserRole


def _intent_json(**overrides) -> str:
    payload = {
        "needs_regulatory_search": False,
        "needs_inspection_guideline_search": False,
        "search_query": "",
        "needs_business_context": False,
        "needs_complaint_history": False,
        "needs_inspection_history": False,
        "needs_evidence_analysis": False,
    }
    payload.update(overrides)
    return json.dumps(payload)


def _answer_json(**overrides) -> str:
    payload = {"answer": "Here is the answer.", "used_source_ids": [], "is_uncertain": False, "uncertainty_reason": None}
    payload.update(overrides)
    return json.dumps(payload)


def _queue_gemini(monkeypatch, *responses) -> None:
    calls = {"i": 0}

    def _fake(prompt, response_schema):
        value = responses[calls["i"]]
        calls["i"] += 1
        return value

    monkeypatch.setattr(ai_service, "generate_structured_json", _fake)


def _setup(db_session: Session):
    division = create_division(db_session, name="Pune Division", code="PUN")
    pune = create_district(db_session, division, name="Pune", code="PUN")

    pune_inspector, inspector_staff = create_staff(
        db_session, pune, role=UserRole.INSPECTOR, email="pune.inspector@example.com", employee_code="INS-PUN"
    )
    other_inspector, other_inspector_staff = create_staff(
        db_session, pune, role=UserRole.INSPECTOR, email="other.inspector@example.com", employee_code="INS-PUN-2"
    )
    pune_officer, _officer_staff = create_staff(
        db_session, pune, role=UserRole.DISTRICT_OFFICER, email="pune.officer@example.com", employee_code="DO-PUN"
    )

    category = create_complaint_category(db_session, key="expired_food", name="Expired Food")
    citizen = create_user(db_session, email="citizen@example.com")
    business = create_business(db_session, pune, business_name="Shree Dairy")
    complaint = create_complaint(
        db_session, citizen, pune, category, business=business, complaint_number="MH-PUN-2026-000001"
    )
    other_complaint = create_complaint(
        db_session, citizen, pune, category, business=business, complaint_number="MH-PUN-2026-000002"
    )
    inspection = create_inspection(db_session, complaint, inspector_staff)
    other_inspection = create_inspection(db_session, other_complaint, other_inspector_staff)

    return pune_inspector, other_inspector, pune_officer, citizen, inspection, other_inspection


def test_inspector_can_create_general_conversation(client: TestClient, db_session: Session) -> None:
    inspector, _other, _officer, _citizen, _inspection, _other_inspection = _setup(db_session)

    response = client.post(
        "/api/v1/inspector/assistant/conversations", headers=auth_headers(inspector), json={}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["inspection_id"] is None
    assert body["messages"] == []


def test_inspector_can_create_case_scoped_conversation(client: TestClient, db_session: Session) -> None:
    inspector, _other, _officer, _citizen, inspection, _other_inspection = _setup(db_session)

    response = client.post(
        "/api/v1/inspector/assistant/conversations",
        headers=auth_headers(inspector),
        json={"inspection_id": str(inspection.id)},
    )

    assert response.status_code == 201
    assert response.json()["inspection_id"] == str(inspection.id)


def test_inspector_cannot_create_conversation_for_another_inspectors_inspection(
    client: TestClient, db_session: Session
) -> None:
    _inspector, other_inspector, _officer, _citizen, inspection, _other_inspection = _setup(db_session)

    response = client.post(
        "/api/v1/inspector/assistant/conversations",
        headers=auth_headers(other_inspector),
        json={"inspection_id": str(inspection.id)},
    )

    assert response.status_code == 404


def test_inspector_cannot_read_another_inspectors_conversation(client: TestClient, db_session: Session) -> None:
    inspector, other_inspector, _officer, _citizen, _inspection, _other_inspection = _setup(db_session)
    create_response = client.post(
        "/api/v1/inspector/assistant/conversations", headers=auth_headers(inspector), json={}
    )
    conversation_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/inspector/assistant/conversations/{conversation_id}", headers=auth_headers(other_inspector)
    )

    assert response.status_code == 404


def test_officer_cannot_use_inspector_assistant_endpoints(client: TestClient, db_session: Session) -> None:
    _inspector, _other, officer, _citizen, _inspection, _other_inspection = _setup(db_session)

    response = client.post("/api/v1/inspector/assistant/conversations", headers=auth_headers(officer), json={})

    assert response.status_code == 403


def test_unauthenticated_request_is_rejected(client: TestClient) -> None:
    response = client.post("/api/v1/inspector/assistant/conversations", json={})

    assert response.status_code == 401


def test_end_to_end_ask_returns_answer_with_citations(client: TestClient, db_session: Session, monkeypatch) -> None:
    from app.agents.inspector_assistant import tools
    from app.rag.retrieval import RetrievedChunk

    inspector, _other, _officer, _citizen, _inspection, _other_inspection = _setup(db_session)
    chunk = RetrievedChunk(
        chunk_id="c1",
        document_id="00000000-0000-0000-0000-0000000000aa",
        document_title="FSSAI Hygiene Guidelines",
        source_organization="FSSAI",
        document_type="hygiene_guideline",
        page_number=5,
        section_title="Personal Hygiene",
        content="Food handlers must wash hands before handling food.",
        score=0.95,
    )
    monkeypatch.setattr(tools, "search_regulations", lambda *a, **k: [chunk])
    _queue_gemini(
        monkeypatch,
        _intent_json(needs_regulatory_search=True, search_query="hand hygiene"),
        _answer_json(answer="Wash hands before handling food, per FSSAI guidance.", used_source_ids=["R1"]),
    )

    create_response = client.post(
        "/api/v1/inspector/assistant/conversations", headers=auth_headers(inspector), json={}
    )
    conversation_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/inspector/assistant/conversations/{conversation_id}/messages",
        headers=auth_headers(inspector),
        json={"question": "What are the hand hygiene requirements?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "assistant"
    assert "Wash hands" in body["content"]
    assert body["citations"][0]["title"] == "FSSAI Hygiene Guidelines"
    assert body["citations"][0]["page_number"] == 5


def test_empty_knowledge_base_states_insufficient_information(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    from app.agents.inspector_assistant import tools

    inspector, _other, _officer, _citizen, _inspection, _other_inspection = _setup(db_session)
    monkeypatch.setattr(tools, "search_regulations", lambda *a, **k: [])
    _queue_gemini(
        monkeypatch,
        _intent_json(needs_regulatory_search=True, search_query="obscure regulation"),
        _answer_json(answer="I could not find this in the knowledge base.", used_source_ids=[]),
    )

    create_response = client.post(
        "/api/v1/inspector/assistant/conversations", headers=auth_headers(inspector), json={}
    )
    conversation_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/inspector/assistant/conversations/{conversation_id}/messages",
        headers=auth_headers(inspector),
        json={"question": "What does obscure regulation X say?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["is_uncertain"] is True
    assert body["citations"] == []


def test_gemini_failure_returns_clean_error_message_not_fabricated_200(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    from app.utils.exceptions import GeminiUnavailableError

    inspector, _other, _officer, _citizen, _inspection, _other_inspection = _setup(db_session)

    def _raise(*a, **k):
        raise GeminiUnavailableError()

    monkeypatch.setattr(ai_service, "generate_structured_json", _raise)
    from app.agents.inspector_assistant import agent as inspector_assistant_agent

    monkeypatch.setattr(inspector_assistant_agent.time, "sleep", lambda *a, **k: None)

    create_response = client.post(
        "/api/v1/inspector/assistant/conversations", headers=auth_headers(inspector), json={}
    )
    conversation_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/inspector/assistant/conversations/{conversation_id}/messages",
        headers=auth_headers(inspector),
        json={"question": "Any question"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["error_code"] == "GEMINI_UNAVAILABLE"


def test_malformed_ai_response_returns_502(client: TestClient, db_session: Session, monkeypatch) -> None:
    inspector, _other, _officer, _citizen, _inspection, _other_inspection = _setup(db_session)
    monkeypatch.setattr(ai_service, "generate_structured_json", lambda *a, **k: "not json")

    create_response = client.post(
        "/api/v1/inspector/assistant/conversations", headers=auth_headers(inspector), json={}
    )
    conversation_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/inspector/assistant/conversations/{conversation_id}/messages",
        headers=auth_headers(inspector),
        json={"question": "Any question"},
    )

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "INVALID_AI_RESPONSE"


def test_conversation_supports_follow_up_questions(client: TestClient, db_session: Session, monkeypatch) -> None:
    inspector, _other, _officer, _citizen, _inspection, _other_inspection = _setup(db_session)
    _queue_gemini(
        monkeypatch,
        _intent_json(),
        _answer_json(answer="First answer."),
        _intent_json(),
        _answer_json(answer="Second answer, building on the first."),
    )

    create_response = client.post(
        "/api/v1/inspector/assistant/conversations", headers=auth_headers(inspector), json={}
    )
    conversation_id = create_response.json()["id"]

    first = client.post(
        f"/api/v1/inspector/assistant/conversations/{conversation_id}/messages",
        headers=auth_headers(inspector),
        json={"question": "First question"},
    )
    second = client.post(
        f"/api/v1/inspector/assistant/conversations/{conversation_id}/messages",
        headers=auth_headers(inspector),
        json={"question": "Follow-up question"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["content"] == "Second answer, building on the first."

    full = client.get(
        f"/api/v1/inspector/assistant/conversations/{conversation_id}", headers=auth_headers(inspector)
    )
    assert len(full.json()["messages"]) == 4
