from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.tests.factories import (
    auth_headers,
    create_complaint,
    create_complaint_category,
    create_district,
    create_division,
    create_user,
)
from app.utils.enums import ComplaintStatus, UserRole


def _setup(db_session: Session) -> dict:
    division = create_division(db_session, name="Pune Division", code="PUN")
    pune = create_district(db_session, division, name="Pune", code="PUN")
    nagpur = create_district(db_session, division, name="Nagpur", code="NGP")

    category = create_complaint_category(db_session)
    citizen = create_user(db_session, email="citizen@example.com")
    admin = create_user(db_session, email="admin@example.com", role=UserRole.ADMIN)

    create_complaint(db_session, citizen, pune, category, status=ComplaintStatus.SUBMITTED)
    create_complaint(db_session, citizen, pune, category, status=ComplaintStatus.VERIFIED)
    create_complaint(db_session, citizen, nagpur, category, status=ComplaintStatus.RESOLVED)

    return {"pune": pune, "nagpur": nagpur, "admin": admin}


def test_statewide_analytics_aggregates_all_districts(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)

    response = client.get("/api/v1/admin/analytics", headers=auth_headers(ctx["admin"]))

    assert response.status_code == 200
    body = response.json()
    assert body["total_complaints"] == 3
    assert body["pending_complaints"] == 1
    assert body["active_complaints"] == 1
    assert body["resolved_complaints"] == 1
    assert body["total_districts"] == 2

    breakdown = {item["district_name"]: item for item in body["district_breakdown"]}
    assert breakdown["Pune"]["total_complaints"] == 2
    assert breakdown["Pune"]["pending_complaints"] == 1
    assert breakdown["Pune"]["active_complaints"] == 1
    assert breakdown["Nagpur"]["total_complaints"] == 1
    assert breakdown["Nagpur"]["resolved_complaints"] == 1
    assert breakdown["Pune"]["division_name"] == "Pune Division"


def test_district_with_no_complaints_still_appears_with_zero_counts(client: TestClient, db_session: Session) -> None:
    division = create_division(db_session, name="Konkan Division", code="KON")
    create_district(db_session, division, name="Raigad", code="RAI")
    admin = create_user(db_session, email="admin2@example.com", role=UserRole.ADMIN)

    response = client.get("/api/v1/admin/analytics", headers=auth_headers(admin))

    assert response.status_code == 200
    breakdown = {item["district_name"]: item for item in response.json()["district_breakdown"]}
    assert breakdown["Raigad"]["total_complaints"] == 0


def test_non_admin_cannot_access_admin_analytics(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)
    citizen = create_user(db_session, email="plain-citizen@example.com")

    response = client.get("/api/v1/admin/analytics", headers=auth_headers(citizen))

    assert response.status_code == 403


def test_unauthenticated_cannot_access_admin_analytics(client: TestClient) -> None:
    response = client.get("/api/v1/admin/analytics")

    assert response.status_code == 401
