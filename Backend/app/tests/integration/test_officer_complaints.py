from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

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
from app.utils.enums import ComplaintStatus, UserRole


def _setup_two_districts(db_session: Session):
    division = create_division(db_session, name="Pune Division", code="PUN")
    pune = create_district(db_session, division, name="Pune", code="PUN")
    nagpur = create_district(db_session, division, name="Nagpur", code="NGP")

    pune_officer, _ = create_staff(
        db_session, pune, role=UserRole.DISTRICT_OFFICER, email="pune.officer@example.com", employee_code="DO-PUN"
    )
    nagpur_officer, _ = create_staff(
        db_session, nagpur, role=UserRole.DISTRICT_OFFICER, email="nagpur.officer@example.com", employee_code="DO-NGP"
    )

    category = create_complaint_category(db_session, key="expired_food", name="Expired Food")
    citizen = create_user(db_session, email="citizen@example.com", full_name="Asha Citizen")

    pune_business = create_business(db_session, pune, business_name="Pune Grocer")
    nagpur_business = create_business(db_session, nagpur, business_name="Nagpur Grocer")

    pune_complaint = create_complaint(
        db_session, citizen, pune, category, business=pune_business, complaint_number="MH-PUN-2026-000001"
    )
    nagpur_complaint = create_complaint(
        db_session, citizen, nagpur, category, business=nagpur_business, complaint_number="MH-NGP-2026-000001"
    )

    return pune, nagpur, pune_officer, nagpur_officer, pune_complaint, nagpur_complaint


def test_officer_queue_is_scoped_to_own_district(client: TestClient, db_session: Session) -> None:
    pune, nagpur, pune_officer, nagpur_officer, pune_complaint, nagpur_complaint = _setup_two_districts(db_session)

    response = client.get("/api/v1/officer/complaints", headers=auth_headers(pune_officer))

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == str(pune_complaint.id)


def test_officer_cannot_view_complaint_from_another_district(client: TestClient, db_session: Session) -> None:
    pune, nagpur, pune_officer, nagpur_officer, pune_complaint, nagpur_complaint = _setup_two_districts(db_session)

    response = client.get(f"/api/v1/officer/complaints/{nagpur_complaint.id}", headers=auth_headers(pune_officer))

    assert response.status_code == 404


def test_officer_can_view_own_district_complaint_detail(client: TestClient, db_session: Session) -> None:
    pune, nagpur, pune_officer, nagpur_officer, pune_complaint, nagpur_complaint = _setup_two_districts(db_session)

    response = client.get(f"/api/v1/officer/complaints/{pune_complaint.id}", headers=auth_headers(pune_officer))

    assert response.status_code == 200
    assert response.json()["id"] == str(pune_complaint.id)


def test_status_update_happy_path_records_history(client: TestClient, db_session: Session) -> None:
    pune, nagpur, pune_officer, nagpur_officer, pune_complaint, nagpur_complaint = _setup_two_districts(db_session)

    response = client.patch(
        f"/api/v1/officer/complaints/{pune_complaint.id}/status",
        json={"status": "under_review", "reason": "Starting review."},
        headers=auth_headers(pune_officer),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "under_review"

    timeline = client.get(
        f"/api/v1/officer/complaints/{pune_complaint.id}/timeline", headers=auth_headers(pune_officer)
    )
    entries = timeline.json()
    # The factory-created complaint has no initial "submitted" history row
    # (that's written by the create_complaint service, not the factory), so
    # this status update is the only entry.
    assert len(entries) == 1
    assert entries[-1]["old_status"] == "submitted"
    assert entries[-1]["new_status"] == "under_review"
    assert entries[-1]["reason"] == "Starting review."


def test_invalid_status_transition_is_rejected(client: TestClient, db_session: Session) -> None:
    pune, nagpur, pune_officer, nagpur_officer, pune_complaint, nagpur_complaint = _setup_two_districts(db_session)

    # SUBMITTED -> RESOLVED is not an allowed transition in this phase.
    response = client.patch(
        f"/api/v1/officer/complaints/{pune_complaint.id}/status",
        json={"status": "resolved"},
        headers=auth_headers(pune_officer),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"


def test_officer_cannot_update_status_of_another_districts_complaint(client: TestClient, db_session: Session) -> None:
    pune, nagpur, pune_officer, nagpur_officer, pune_complaint, nagpur_complaint = _setup_two_districts(db_session)

    response = client.patch(
        f"/api/v1/officer/complaints/{nagpur_complaint.id}/status",
        json={"status": "under_review"},
        headers=auth_headers(pune_officer),
    )

    assert response.status_code == 404
