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
from app.utils.enums import ComplaintPriority, ComplaintStatus, UserRole


def _setup(db_session: Session):
    division = create_division(db_session)
    pune = create_district(
        db_session, division, name="Pune", code="PUN", centroid_latitude=18.5204, centroid_longitude=73.8567
    )
    nagpur = create_district(
        db_session, division, name="Nagpur", code="NGP", centroid_latitude=21.1458, centroid_longitude=79.0882
    )
    pune_officer, _ = create_staff(
        db_session, pune, role=UserRole.DISTRICT_OFFICER, email="pune.officer@example.com", employee_code="DO-PUN"
    )
    nagpur_officer, _ = create_staff(
        db_session, nagpur, role=UserRole.DISTRICT_OFFICER, email="nagpur.officer@example.com", employee_code="DO-NGP"
    )
    category = create_complaint_category(db_session)
    citizen = create_user(db_session, email="citizen@example.com")

    pune_complaint_high = create_complaint(
        db_session,
        citizen,
        pune,
        category,
        title="Pune high priority",
        priority=ComplaintPriority.HIGH,
        latitude=18.52,
        longitude=73.86,
    )
    pune_complaint_low = create_complaint(
        db_session,
        citizen,
        pune,
        category,
        title="Pune low priority",
        priority=ComplaintPriority.LOW,
        latitude=18.60,
        longitude=73.90,
    )
    pune_complaint_no_location = create_complaint(
        db_session, citizen, pune, category, title="Pune no location"
    )
    nagpur_complaint = create_complaint(
        db_session,
        citizen,
        nagpur,
        category,
        title="Nagpur complaint",
        latitude=21.15,
        longitude=79.09,
    )

    return {
        "pune": pune,
        "nagpur": nagpur,
        "pune_officer": pune_officer,
        "nagpur_officer": nagpur_officer,
        "category": category,
        "pune_complaint_high": pune_complaint_high,
        "pune_complaint_low": pune_complaint_low,
        "pune_complaint_no_location": pune_complaint_no_location,
        "nagpur_complaint": nagpur_complaint,
    }


def test_map_only_returns_complaints_with_coordinates(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)

    response = client.get("/api/v1/officer/complaints/map", headers=auth_headers(ctx["pune_officer"]))

    assert response.status_code == 200
    body = response.json()
    ids = {item["id"] for item in body["items"]}
    assert str(ctx["pune_complaint_high"].id) in ids
    assert str(ctx["pune_complaint_low"].id) in ids
    assert str(ctx["pune_complaint_no_location"].id) not in ids


def test_map_is_district_isolated(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)

    response = client.get("/api/v1/officer/complaints/map", headers=auth_headers(ctx["pune_officer"]))

    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["items"]}
    assert str(ctx["nagpur_complaint"].id) not in ids


def test_map_scope_cannot_be_overridden_by_query_params(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)

    # The map endpoint takes no district_id parameter - scope always comes
    # from the authenticated officer's own staff profile.
    response = client.get(
        "/api/v1/officer/complaints/map",
        params={"district_id": str(ctx["nagpur"].id)},
        headers=auth_headers(ctx["pune_officer"]),
    )

    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["items"]}
    assert str(ctx["nagpur_complaint"].id) not in ids
    assert str(ctx["pune_complaint_high"].id) in ids


def test_map_filters_by_priority(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)

    response = client.get(
        "/api/v1/officer/complaints/map",
        params={"priority": "high"},
        headers=auth_headers(ctx["pune_officer"]),
    )

    assert response.status_code == 200
    items = response.json()["items"]
    assert {item["id"] for item in items} == {str(ctx["pune_complaint_high"].id)}


def test_map_filters_by_bounding_box(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)

    # A tight box around the "high priority" marker only.
    response = client.get(
        "/api/v1/officer/complaints/map",
        params={"min_lat": 18.51, "max_lat": 18.53, "min_lng": 73.85, "max_lng": 73.87},
        headers=auth_headers(ctx["pune_officer"]),
    )

    assert response.status_code == 200
    items = response.json()["items"]
    assert {item["id"] for item in items} == {str(ctx["pune_complaint_high"].id)}


def test_map_requires_district_officer_role(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)
    citizen = create_user(db_session, email="plain.citizen@example.com")

    response = client.get(
        "/api/v1/officer/complaints/map",
        headers=auth_headers(citizen),
    )

    assert response.status_code == 403


def test_nearby_endpoint_is_district_scoped(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)

    response = client.get(
        "/api/v1/officer/complaints/nearby",
        params={"latitude": 18.52, "longitude": 73.86, "radius_km": 50},
        headers=auth_headers(ctx["pune_officer"]),
    )

    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert str(ctx["pune_complaint_high"].id) in ids
    assert str(ctx["nagpur_complaint"].id) not in ids
