from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.tests.factories import (
    auth_headers,
    create_complaint_category,
    create_district,
    create_division,
    create_staff,
    create_user,
)
from app.utils.enums import UserRole


def _setup(db_session: Session):
    division = create_division(db_session, name="Pune Division", code="PUN")
    pune = create_district(db_session, division, name="Pune", code="PUN")

    officer, officer_profile = create_staff(
        db_session, pune, role=UserRole.DISTRICT_OFFICER, email="officer@example.com", employee_code="DO-1"
    )
    inspector, inspector_profile = create_staff(
        db_session, pune, role=UserRole.INSPECTOR, email="inspector@example.com", employee_code="INS-1"
    )
    category = create_complaint_category(db_session)
    citizen = create_user(db_session, email="citizen@example.com")

    return {
        "district": pune,
        "officer": officer,
        "officer_profile": officer_profile,
        "inspector": inspector,
        "inspector_profile": inspector_profile,
        "category": category,
        "citizen": citizen,
    }


def _create_complaint(client: TestClient, ctx: dict) -> dict:
    response = client.post(
        "/api/v1/complaints",
        headers=auth_headers(ctx["citizen"]),
        json={
            "category_id": str(ctx["category"].id),
            "district_id": str(ctx["district"].id),
            "title": "Expired products on shelf",
            "description": "Found several expired dairy products still on display.",
            "business": {"business_name": "Test Store", "address": "1 Market Road"},
        },
    )
    assert response.status_code == 201
    return response.json()


def test_complaint_submission_notifies_citizen_and_district_officers(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)

    complaint = _create_complaint(client, ctx)

    citizen_notifications = client.get("/api/v1/notifications", headers=auth_headers(ctx["citizen"])).json()
    assert citizen_notifications["total"] == 1
    assert citizen_notifications["items"][0]["type"] == "complaint_submitted"
    assert complaint["complaint_number"] in citizen_notifications["items"][0]["message"]

    officer_notifications = client.get("/api/v1/notifications", headers=auth_headers(ctx["officer"])).json()
    assert officer_notifications["total"] == 1
    assert officer_notifications["items"][0]["type"] == "complaint_submitted"
    assert officer_notifications["items"][0]["entity_id"] == complaint["id"]


def test_full_workflow_fires_expected_notification_types(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)
    complaint = _create_complaint(client, ctx)
    complaint_id = complaint["id"]

    client.patch(
        f"/api/v1/officer/complaints/{complaint_id}/status",
        json={"status": "under_review"},
        headers=auth_headers(ctx["officer"]),
    )
    client.patch(
        f"/api/v1/officer/complaints/{complaint_id}/status",
        json={"status": "verified"},
        headers=auth_headers(ctx["officer"]),
    )
    client.post(
        f"/api/v1/officer/complaints/{complaint_id}/assign",
        json={"inspector_staff_id": str(ctx["inspector_profile"].id)},
        headers=auth_headers(ctx["officer"]),
    )
    inspection = client.post(
        "/api/v1/inspector/inspections",
        json={"complaint_id": complaint_id},
        headers=auth_headers(ctx["inspector"]),
    ).json()
    client.patch(
        f"/api/v1/inspector/inspections/{inspection['id']}",
        json={"status": "in_progress"},
        headers=auth_headers(ctx["inspector"]),
    )
    client.post(
        f"/api/v1/inspector/inspections/{inspection['id']}/complete",
        json={"summary": "All good.", "action_recommended": "None."},
        headers=auth_headers(ctx["inspector"]),
    )
    client.patch(
        f"/api/v1/officer/complaints/{complaint_id}/status",
        json={"status": "resolved"},
        headers=auth_headers(ctx["officer"]),
    )

    citizen_notifications = client.get(
        "/api/v1/notifications", params={"page_size": 50}, headers=auth_headers(ctx["citizen"])
    ).json()
    citizen_types = [item["type"] for item in citizen_notifications["items"]]
    # under_review is not a notification-worthy status, so it should not appear.
    assert citizen_types.count("complaint_submitted") == 1
    assert "complaint_verified" in citizen_types
    assert "inspector_assigned" in citizen_types
    assert "inspection_scheduled" in citizen_types
    assert "inspection_completed" in citizen_types
    assert "complaint_resolved" in citizen_types

    inspector_notifications = client.get("/api/v1/notifications", headers=auth_headers(ctx["inspector"])).json()
    assert any(item["type"] == "inspector_assigned" for item in inspector_notifications["items"])


def test_rejected_complaint_notifies_citizen(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)
    complaint = _create_complaint(client, ctx)

    client.patch(
        f"/api/v1/officer/complaints/{complaint['id']}/status",
        json={"status": "under_review"},
        headers=auth_headers(ctx["officer"]),
    )
    client.patch(
        f"/api/v1/officer/complaints/{complaint['id']}/status",
        json={"status": "rejected", "reason": "Insufficient detail."},
        headers=auth_headers(ctx["officer"]),
    )

    notifications = client.get("/api/v1/notifications", headers=auth_headers(ctx["citizen"])).json()
    types = [item["type"] for item in notifications["items"]]
    assert "complaint_rejected" in types


def test_unread_count_and_mark_read(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)
    _create_complaint(client, ctx)

    unread = client.get("/api/v1/notifications/unread-count", headers=auth_headers(ctx["citizen"])).json()
    assert unread["unread_count"] == 1

    listing = client.get("/api/v1/notifications", headers=auth_headers(ctx["citizen"])).json()
    notification_id = listing["items"][0]["id"]

    mark_response = client.patch(
        f"/api/v1/notifications/{notification_id}/read", headers=auth_headers(ctx["citizen"])
    )
    assert mark_response.status_code == 200
    assert mark_response.json()["is_read"] is True

    unread_after = client.get("/api/v1/notifications/unread-count", headers=auth_headers(ctx["citizen"])).json()
    assert unread_after["unread_count"] == 0


def test_mark_all_read(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)
    _create_complaint(client, ctx)
    _create_complaint(client, ctx)

    response = client.post("/api/v1/notifications/read-all", headers=auth_headers(ctx["citizen"]))
    assert response.status_code == 200
    assert response.json()["marked_count"] == 2

    unread = client.get("/api/v1/notifications/unread-count", headers=auth_headers(ctx["citizen"])).json()
    assert unread["unread_count"] == 0


def test_user_cannot_read_or_mark_another_users_notification(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)
    _create_complaint(client, ctx)

    other_citizen = create_user(db_session, email="other-citizen@example.com")

    other_listing = client.get("/api/v1/notifications", headers=auth_headers(other_citizen)).json()
    assert other_listing["total"] == 0

    citizen_listing = client.get("/api/v1/notifications", headers=auth_headers(ctx["citizen"])).json()
    notification_id = citizen_listing["items"][0]["id"]

    response = client.patch(
        f"/api/v1/notifications/{notification_id}/read", headers=auth_headers(other_citizen)
    )
    assert response.status_code == 404


def test_unauthenticated_cannot_list_notifications(client: TestClient) -> None:
    response = client.get("/api/v1/notifications")

    assert response.status_code == 401
