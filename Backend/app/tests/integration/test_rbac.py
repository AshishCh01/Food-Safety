from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.staff_profile import StaffProfile
from app.tests.factories import auth_headers, create_district, create_division, create_staff, create_user
from app.utils.enums import UserRole


def test_citizen_cannot_access_admin_endpoints(client: TestClient, db_session: Session) -> None:
    citizen = create_user(db_session, email="citizen@example.com", role=UserRole.CITIZEN)

    response = client.get("/api/v1/admin/districts", headers=auth_headers(citizen))

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


def test_citizen_cannot_access_officer_endpoints(client: TestClient, db_session: Session) -> None:
    citizen = create_user(db_session, email="citizen2@example.com", role=UserRole.CITIZEN)

    response = client.get("/api/v1/officer/dashboard", headers=auth_headers(citizen))

    assert response.status_code == 403


def test_citizen_cannot_access_inspector_endpoints(client: TestClient, db_session: Session) -> None:
    citizen = create_user(db_session, email="citizen3@example.com", role=UserRole.CITIZEN)

    response = client.get("/api/v1/inspector/dashboard", headers=auth_headers(citizen))

    assert response.status_code == 403


def test_inspector_cannot_access_admin_endpoints(client: TestClient, db_session: Session) -> None:
    division = create_division(db_session)
    district = create_district(db_session, division)
    inspector_user, _ = create_staff(
        db_session, district, role=UserRole.INSPECTOR, email="insp@example.com", employee_code="INS-1"
    )

    response = client.post(
        "/api/v1/admin/staff",
        headers=auth_headers(inspector_user),
        json={
            "email": "new@example.com",
            "password": "Password123!",
            "full_name": "New Staff",
            "role": "inspector",
            "district_id": str(district.id),
            "employee_code": "INS-2",
        },
    )

    assert response.status_code == 403


def test_district_officer_cannot_access_inspector_endpoints(client: TestClient, db_session: Session) -> None:
    division = create_division(db_session)
    district = create_district(db_session, division)
    officer_user, _ = create_staff(
        db_session, district, role=UserRole.DISTRICT_OFFICER, email="officer@example.com", employee_code="DO-1"
    )

    response = client.get("/api/v1/inspector/dashboard", headers=auth_headers(officer_user))

    assert response.status_code == 403


def test_inspector_cannot_access_officer_endpoints(client: TestClient, db_session: Session) -> None:
    division = create_division(db_session)
    district = create_district(db_session, division)
    inspector_user, _ = create_staff(
        db_session, district, role=UserRole.INSPECTOR, email="insp2@example.com", employee_code="INS-3"
    )

    response = client.get("/api/v1/officer/dashboard", headers=auth_headers(inspector_user))

    assert response.status_code == 403


def test_admin_can_access_admin_dashboard(client: TestClient, db_session: Session) -> None:
    admin = create_user(db_session, email="admin@example.com", role=UserRole.ADMIN)

    response = client.get("/api/v1/admin/dashboard", headers=auth_headers(admin))

    assert response.status_code == 200


def test_unauthenticated_request_is_rejected(client: TestClient) -> None:
    response = client.get("/api/v1/admin/districts")

    assert response.status_code == 401


def test_citizen_cannot_access_officer_analytics(client: TestClient, db_session: Session) -> None:
    citizen = create_user(db_session, email="citizen-analytics@example.com", role=UserRole.CITIZEN)

    response = client.get("/api/v1/officer/analytics", headers=auth_headers(citizen))

    assert response.status_code == 403


def test_officer_cannot_access_admin_analytics_or_audit_logs(client: TestClient, db_session: Session) -> None:
    division = create_division(db_session)
    district = create_district(db_session, division)
    officer_user, _ = create_staff(
        db_session, district, role=UserRole.DISTRICT_OFFICER, email="officer-audit@example.com", employee_code="DO-5"
    )

    analytics_response = client.get("/api/v1/admin/analytics", headers=auth_headers(officer_user))
    audit_response = client.get("/api/v1/admin/audit-logs", headers=auth_headers(officer_user))

    assert analytics_response.status_code == 403
    assert audit_response.status_code == 403


def test_inactive_staff_profile_is_denied_even_when_user_account_is_active(
    client: TestClient, db_session: Session
) -> None:
    division = create_division(db_session)
    district = create_district(db_session, division)
    # User account itself is active; only the staff profile is deactivated
    # (e.g. reassigned/offboarded), which must still block staff endpoints.
    inspector_user, profile = create_staff(
        db_session, district, role=UserRole.INSPECTOR, email="inactivestaff@example.com", employee_code="INS-4"
    )
    profile.is_active = False
    db_session.commit()

    response = client.get("/api/v1/inspector/dashboard", headers=auth_headers(inspector_user))

    assert response.status_code == 403
