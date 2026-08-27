from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.tests.factories import (
    auth_headers,
    create_assignment,
    create_complaint,
    create_complaint_category,
    create_district,
    create_division,
    create_staff,
    create_user,
)
from app.utils.enums import ComplaintStatus, UserRole


def _setup(db_session: Session, *, complaint_status: ComplaintStatus = ComplaintStatus.VERIFIED):
    division = create_division(db_session, name="Pune Division", code="PUN")
    pune = create_district(db_session, division, name="Pune", code="PUN")
    nagpur = create_district(db_session, division, name="Nagpur", code="NGP")

    pune_officer, pune_officer_profile = create_staff(
        db_session, pune, role=UserRole.DISTRICT_OFFICER, email="pune.officer@example.com", employee_code="DO-PUN"
    )
    pune_inspector, pune_inspector_profile = create_staff(
        db_session, pune, role=UserRole.INSPECTOR, email="pune.inspector@example.com", employee_code="INS-PUN"
    )
    nagpur_inspector, nagpur_inspector_profile = create_staff(
        db_session, nagpur, role=UserRole.INSPECTOR, email="nagpur.inspector@example.com", employee_code="INS-NGP"
    )

    category = create_complaint_category(db_session)
    citizen = create_user(db_session, email="citizen@example.com")
    complaint = create_complaint(db_session, citizen, pune, category, status=complaint_status)

    return {
        "pune": pune,
        "nagpur": nagpur,
        "pune_officer": pune_officer,
        "pune_officer_profile": pune_officer_profile,
        "pune_inspector": pune_inspector,
        "pune_inspector_profile": pune_inspector_profile,
        "nagpur_inspector": nagpur_inspector,
        "nagpur_inspector_profile": nagpur_inspector_profile,
        "complaint": complaint,
    }


def test_officer_assigns_inspector_in_own_district(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)

    response = client.post(
        f"/api/v1/officer/complaints/{ctx['complaint'].id}/assign",
        json={"inspector_staff_id": str(ctx["pune_inspector_profile"].id), "notes": "Please inspect promptly."},
        headers=auth_headers(ctx["pune_officer"]),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["inspector_staff_id"] == str(ctx["pune_inspector_profile"].id)
    assert body["status"] == "assigned"
    assert body["complaint"]["status"] == "assigned"


def test_officer_cannot_assign_inspector_from_another_district(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)

    response = client.post(
        f"/api/v1/officer/complaints/{ctx['complaint'].id}/assign",
        json={"inspector_staff_id": str(ctx["nagpur_inspector_profile"].id)},
        headers=auth_headers(ctx["pune_officer"]),
    )

    assert response.status_code == 404


def test_cannot_assign_non_inspector_staff(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)

    response = client.post(
        f"/api/v1/officer/complaints/{ctx['complaint'].id}/assign",
        json={"inspector_staff_id": str(ctx["pune_officer_profile"].id)},
        headers=auth_headers(ctx["pune_officer"]),
    )

    assert response.status_code == 404


def test_cannot_assign_non_verified_complaint(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session, complaint_status=ComplaintStatus.SUBMITTED)

    response = client.post(
        f"/api/v1/officer/complaints/{ctx['complaint'].id}/assign",
        json={"inspector_staff_id": str(ctx["pune_inspector_profile"].id)},
        headers=auth_headers(ctx["pune_officer"]),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_ASSIGNMENT"


def test_double_assignment_is_blocked(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)
    payload = {"inspector_staff_id": str(ctx["pune_inspector_profile"].id)}

    first = client.post(
        f"/api/v1/officer/complaints/{ctx['complaint'].id}/assign", json=payload, headers=auth_headers(ctx["pune_officer"])
    )
    assert first.status_code == 201

    second = client.post(
        f"/api/v1/officer/complaints/{ctx['complaint'].id}/assign", json=payload, headers=auth_headers(ctx["pune_officer"])
    )
    assert second.status_code == 409


def test_officer_from_other_district_cannot_view_assignment(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)
    nagpur_officer, _ = create_staff(
        db_session,
        ctx["nagpur"],
        role=UserRole.DISTRICT_OFFICER,
        email="nagpur.officer@example.com",
        employee_code="DO-NGP",
    )
    create_assignment(db_session, ctx["complaint"], ctx["pune_inspector_profile"], ctx["pune_officer_profile"])

    response = client.get(
        f"/api/v1/officer/complaints/{ctx['complaint'].id}/assignment", headers=auth_headers(nagpur_officer)
    )

    assert response.status_code == 404


def test_inspector_sees_own_assignments_list_and_detail(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)
    assignment = create_assignment(db_session, ctx["complaint"], ctx["pune_inspector_profile"], ctx["pune_officer_profile"])

    list_response = client.get("/api/v1/inspector/assignments", headers=auth_headers(ctx["pune_inspector"]))
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    detail_response = client.get(
        f"/api/v1/inspector/assignments/{assignment.id}", headers=auth_headers(ctx["pune_inspector"])
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["complaint"]["id"] == str(ctx["complaint"].id)
    assert detail_response.json()["inspection"] is None


def test_other_inspector_cannot_view_assignment(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)
    assignment = create_assignment(db_session, ctx["complaint"], ctx["pune_inspector_profile"], ctx["pune_officer_profile"])

    response = client.get(
        f"/api/v1/inspector/assignments/{assignment.id}", headers=auth_headers(ctx["nagpur_inspector"])
    )

    assert response.status_code == 404
