from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.tests.factories import (
    auth_headers,
    create_complaint,
    create_complaint_category,
    create_district,
    create_division,
    create_staff,
    create_user,
)
from app.utils.enums import ComplaintStatus, UserRole


def _setup(db_session: Session) -> dict:
    division = create_division(db_session, name="Pune Division", code="PUN")
    pune = create_district(db_session, division, name="Pune", code="PUN")
    officer, officer_profile = create_staff(
        db_session, pune, role=UserRole.DISTRICT_OFFICER, email="officer@example.com", employee_code="DO-1"
    )
    category = create_complaint_category(db_session)
    citizen = create_user(db_session, email="citizen@example.com")
    admin = create_user(db_session, email="admin@example.com", role=UserRole.ADMIN)
    complaint = create_complaint(db_session, citizen, pune, category, status=ComplaintStatus.SUBMITTED)

    return {
        "pune": pune,
        "officer": officer,
        "officer_profile": officer_profile,
        "citizen": citizen,
        "admin": admin,
        "complaint": complaint,
    }


def test_complaint_status_change_creates_audit_record(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)

    client.patch(
        f"/api/v1/officer/complaints/{ctx['complaint'].id}/status",
        json={"status": "under_review"},
        headers=auth_headers(ctx["officer"]),
    )

    response = client.get(
        "/api/v1/admin/audit-logs",
        params={"entity_type": "complaint", "entity_id": str(ctx["complaint"].id)},
        headers=auth_headers(ctx["admin"]),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    entry = body["items"][0]
    assert entry["action"] == "complaint_status_changed"
    assert entry["actor_user_id"] == str(ctx["officer"].id)
    assert entry["details"]["new_status"] == "under_review"


def test_staff_creation_creates_audit_record(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)

    create_response = client.post(
        "/api/v1/admin/staff",
        headers=auth_headers(ctx["admin"]),
        json={
            "email": "new.inspector@example.com",
            "password": "Password123!",
            "full_name": "New Inspector",
            "role": "inspector",
            "district_id": str(ctx["pune"].id),
            "employee_code": "INS-NEW",
        },
    )
    assert create_response.status_code == 201
    staff_id = create_response.json()["id"]

    response = client.get(
        "/api/v1/admin/audit-logs",
        params={"action": "staff_account_created"},
        headers=auth_headers(ctx["admin"]),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["entity_id"] == staff_id
    assert body["items"][0]["actor_user_id"] == str(ctx["admin"].id)


def test_user_status_update_creates_audit_record(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)

    client.patch(
        f"/api/v1/admin/users/{ctx['citizen'].id}/status",
        json={"is_active": False},
        headers=auth_headers(ctx["admin"]),
    )

    response = client.get(
        "/api/v1/admin/audit-logs",
        params={"action": "user_status_updated", "entity_id": str(ctx["citizen"].id)},
        headers=auth_headers(ctx["admin"]),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["details"] == {"is_active": False}


def test_audit_log_filters_by_actor(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)
    client.patch(
        f"/api/v1/officer/complaints/{ctx['complaint'].id}/status",
        json={"status": "under_review"},
        headers=auth_headers(ctx["officer"]),
    )
    client.patch(
        f"/api/v1/admin/users/{ctx['citizen'].id}/status",
        json={"is_active": False},
        headers=auth_headers(ctx["admin"]),
    )

    response = client.get(
        "/api/v1/admin/audit-logs",
        params={"actor_user_id": str(ctx["officer"].id)},
        headers=auth_headers(ctx["admin"]),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["actor_user_id"] == str(ctx["officer"].id)


def test_non_admin_cannot_list_audit_logs(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)

    response = client.get("/api/v1/admin/audit-logs", headers=auth_headers(ctx["officer"]))

    assert response.status_code == 403


def test_unauthenticated_cannot_list_audit_logs(client: TestClient) -> None:
    response = client.get("/api/v1/admin/audit-logs")

    assert response.status_code == 401


def test_no_route_exists_to_modify_or_delete_audit_logs(client: TestClient, db_session: Session) -> None:
    """Audit logs must be immutable from normal application workflows
    (docs/SECURITY_AND_RBAC.md section 12) - there is no PATCH/PUT/DELETE
    endpoint for them at all, only the read-only listing above."""
    ctx = _setup(db_session)
    client.patch(
        f"/api/v1/officer/complaints/{ctx['complaint'].id}/status",
        json={"status": "under_review"},
        headers=auth_headers(ctx["officer"]),
    )
    logs = client.get("/api/v1/admin/audit-logs", headers=auth_headers(ctx["admin"])).json()
    log_id = logs["items"][0]["id"]

    patch_response = client.patch(f"/api/v1/admin/audit-logs/{log_id}", headers=auth_headers(ctx["admin"]))
    delete_response = client.delete(f"/api/v1/admin/audit-logs/{log_id}", headers=auth_headers(ctx["admin"]))

    assert patch_response.status_code in (404, 405)
    assert delete_response.status_code in (404, 405)
