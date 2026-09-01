from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.tests.factories import auth_headers, create_district, create_division, create_staff, create_user
from app.utils.enums import UserRole


def _admin_headers(db_session: Session) -> dict:
    admin = create_user(db_session, email="root-admin@example.com", role=UserRole.ADMIN)
    return auth_headers(admin)


def test_admin_lists_seeded_districts(client: TestClient, db_session: Session) -> None:
    division = create_division(db_session)
    create_district(db_session, division, name="Pune", code="PUN")
    create_district(db_session, division, name="Nagpur", code="NGP")

    response = client.get("/api/v1/admin/districts", headers=_admin_headers(db_session))

    assert response.status_code == 200
    codes = {item["code"] for item in response.json()}
    assert {"PUN", "NGP"}.issubset(codes)


def test_admin_creates_district_officer(client: TestClient, db_session: Session) -> None:
    division = create_division(db_session)
    district = create_district(db_session, division)

    response = client.post(
        "/api/v1/admin/staff",
        headers=_admin_headers(db_session),
        json={
            "email": "new.officer@example.com",
            "password": "Password123!",
            "full_name": "New Officer",
            "role": "district_officer",
            "district_id": str(district.id),
            "employee_code": "DO-NEW",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["role"] == "district_officer"
    assert body["district_id"] == str(district.id)


def test_admin_cannot_create_second_active_officer_for_same_district(
    client: TestClient, db_session: Session
) -> None:
    division = create_division(db_session)
    district = create_district(db_session, division)
    create_staff(db_session, district, role=UserRole.DISTRICT_OFFICER, email="first.officer@example.com", employee_code="DO-1")

    response = client.post(
        "/api/v1/admin/staff",
        headers=_admin_headers(db_session),
        json={
            "email": "second.officer@example.com",
            "password": "Password123!",
            "full_name": "Second Officer",
            "role": "district_officer",
            "district_id": str(district.id),
            "employee_code": "DO-2",
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


def test_admin_can_create_multiple_inspectors_for_same_district(client: TestClient, db_session: Session) -> None:
    division = create_division(db_session)
    district = create_district(db_session, division)
    create_staff(db_session, district, role=UserRole.INSPECTOR, email="first.inspector@example.com", employee_code="INS-1")

    response = client.post(
        "/api/v1/admin/staff",
        headers=_admin_headers(db_session),
        json={
            "email": "second.inspector@example.com",
            "password": "Password123!",
            "full_name": "Second Inspector",
            "role": "inspector",
            "district_id": str(district.id),
            "employee_code": "INS-2",
        },
    )

    assert response.status_code == 201


def test_admin_staff_creation_rejects_citizen_role(client: TestClient, db_session: Session) -> None:
    division = create_division(db_session)
    district = create_district(db_session, division)

    response = client.post(
        "/api/v1/admin/staff",
        headers=_admin_headers(db_session),
        json={
            "email": "sneaky@example.com",
            "password": "Password123!",
            "full_name": "Sneaky User",
            "role": "citizen",
            "district_id": str(district.id),
            "employee_code": "X-1",
        },
    )

    assert response.status_code == 422


def test_admin_staff_creation_rejects_unknown_district(client: TestClient, db_session: Session) -> None:
    response = client.post(
        "/api/v1/admin/staff",
        headers=_admin_headers(db_session),
        json={
            "email": "nowhere@example.com",
            "password": "Password123!",
            "full_name": "Nowhere User",
            "role": "inspector",
            "district_id": "00000000-0000-0000-0000-000000000000",
            "employee_code": "X-2",
        },
    )

    assert response.status_code == 404


def test_admin_can_deactivate_a_user(client: TestClient, db_session: Session) -> None:
    target = create_user(db_session, email="deactivate-me@example.com")

    response = client.patch(
        f"/api/v1/admin/users/{target.id}/status",
        headers=_admin_headers(db_session),
        json={"is_active": False},
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_deactivated_user_cannot_log_in(client: TestClient, db_session: Session) -> None:
    target = create_user(db_session, email="soon-inactive@example.com", password="Password123!")
    client.patch(
        f"/api/v1/admin/users/{target.id}/status",
        headers=_admin_headers(db_session),
        json={"is_active": False},
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "soon-inactive@example.com", "password": "Password123!"},
    )

    assert response.status_code == 403


def test_admin_users_list_supports_role_filter(client: TestClient, db_session: Session) -> None:
    create_user(db_session, email="citizen-a@example.com", role=UserRole.CITIZEN)
    create_user(db_session, email="citizen-b@example.com", role=UserRole.CITIZEN)

    response = client.get(
        "/api/v1/admin/users",
        params={"role": "citizen"},
        headers=_admin_headers(db_session),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 2
    assert all(item["role"] == "citizen" for item in body["items"])
