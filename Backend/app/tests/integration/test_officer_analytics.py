from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.tests.factories import (
    auth_headers,
    create_assignment,
    create_complaint,
    create_complaint_category,
    create_district,
    create_division,
    create_inspection,
    create_inspection_finding,
    create_staff,
    create_user,
)
from app.utils.enums import AssignmentStatus, ComplaintPriority, ComplaintStatus, InspectionStatus, UserRole


def _setup(db_session: Session) -> dict:
    division = create_division(db_session, name="Pune Division", code="PUN")
    pune = create_district(db_session, division, name="Pune", code="PUN")
    nagpur = create_district(db_session, division, name="Nagpur", code="NGP")

    pune_officer, pune_officer_profile = create_staff(
        db_session, pune, role=UserRole.DISTRICT_OFFICER, email="pune.officer@example.com", employee_code="DO-PUN"
    )
    nagpur_officer, _ = create_staff(
        db_session, nagpur, role=UserRole.DISTRICT_OFFICER, email="nagpur.officer@example.com", employee_code="DO-NGP"
    )
    inspector1, inspector1_profile = create_staff(
        db_session, pune, role=UserRole.INSPECTOR, email="inspector1@example.com", employee_code="INS-1"
    )
    inspector2, inspector2_profile = create_staff(
        db_session, pune, role=UserRole.INSPECTOR, email="inspector2@example.com", employee_code="INS-2"
    )

    category_a = create_complaint_category(db_session, key="expired_food", name="Expired Food")
    category_b = create_complaint_category(db_session, key="unhygienic_premises", name="Unhygienic Premises")
    citizen = create_user(db_session, email="citizen@example.com")

    # Pune complaints - one per KPI bucket.
    pending = create_complaint(
        db_session, citizen, pune, category_a, status=ComplaintStatus.SUBMITTED, priority=ComplaintPriority.HIGH
    )
    active = create_complaint(
        db_session, citizen, pune, category_a, status=ComplaintStatus.VERIFIED, priority=ComplaintPriority.MEDIUM
    )
    resolved = create_complaint(
        db_session, citizen, pune, category_b, status=ComplaintStatus.RESOLVED, priority=ComplaintPriority.LOW
    )
    resolved.resolved_at = resolved.reported_at + timedelta(hours=10)
    db_session.add(resolved)
    db_session.commit()
    rejected = create_complaint(
        db_session, citizen, pune, category_b, status=ComplaintStatus.REJECTED, priority=ComplaintPriority.CRITICAL
    )

    # A complaint in another district must never leak into Pune's analytics.
    create_complaint(db_session, citizen, nagpur, category_a, status=ComplaintStatus.SUBMITTED)

    # Inspector workload: inspector1 has one active + one completed assignment,
    # inspector2 has none.
    create_assignment(db_session, active, inspector1_profile, pune_officer_profile, status=AssignmentStatus.ASSIGNED)
    create_assignment(
        db_session, resolved, inspector1_profile, pune_officer_profile, status=AssignmentStatus.COMPLETED
    )

    # Inspection outcomes: one completed inspection with one compliant and one
    # non-compliant finding, plus one still scheduled.
    completed_inspection = create_inspection(db_session, resolved, inspector1_profile, status=InspectionStatus.COMPLETED)
    create_inspection_finding(db_session, completed_inspection, check_code="A1", compliant=True)
    create_inspection_finding(db_session, completed_inspection, check_code="A2", compliant=False)
    create_inspection(db_session, active, inspector1_profile, status=InspectionStatus.SCHEDULED)

    return {
        "pune": pune,
        "nagpur": nagpur,
        "pune_officer": pune_officer,
        "nagpur_officer": nagpur_officer,
        "inspector1_profile": inspector1_profile,
        "inspector2_profile": inspector2_profile,
    }


def test_district_analytics_reports_expected_kpis(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)

    response = client.get("/api/v1/officer/analytics", headers=auth_headers(ctx["pune_officer"]))

    assert response.status_code == 200
    body = response.json()
    assert body["district_id"] == str(ctx["pune"].id)
    assert body["total_complaints"] == 4
    assert body["pending_complaints"] == 1
    assert body["active_complaints"] == 1
    assert body["resolved_complaints"] == 1
    assert body["rejected_complaints"] == 1
    assert body["average_resolution_hours"] == 10.0

    category_counts = {item["category_name"]: item["count"] for item in body["category_breakdown"]}
    assert category_counts["Expired Food"] == 2
    assert category_counts["Unhygienic Premises"] == 2

    priority_counts = {item["priority"]: item["count"] for item in body["priority_breakdown"]}
    assert priority_counts["high"] == 1
    assert priority_counts["medium"] == 1
    assert priority_counts["low"] == 1
    assert priority_counts["critical"] == 1

    workload_by_id = {item["inspector_staff_id"]: item for item in body["inspector_workload"]}
    inspector1_workload = workload_by_id[str(ctx["inspector1_profile"].id)]
    assert inspector1_workload["total_count"] == 2
    assert inspector1_workload["assigned_count"] == 1
    assert inspector1_workload["completed_count"] == 1
    inspector2_workload = workload_by_id[str(ctx["inspector2_profile"].id)]
    assert inspector2_workload["total_count"] == 0

    outcomes = body["inspection_outcomes"]
    assert outcomes["total_inspections"] == 2
    assert outcomes["completed"] == 1
    assert outcomes["scheduled"] == 1
    assert outcomes["compliant_findings"] == 1
    assert outcomes["non_compliant_findings"] == 1


def test_district_analytics_is_scoped_to_own_district(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)

    response = client.get("/api/v1/officer/analytics", headers=auth_headers(ctx["nagpur_officer"]))

    assert response.status_code == 200
    body = response.json()
    assert body["district_id"] == str(ctx["nagpur"].id)
    assert body["total_complaints"] == 1
    assert body["pending_complaints"] == 1
    assert body["inspector_workload"] == []


def test_complaint_trend_only_includes_recent_days(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)

    response = client.get(
        "/api/v1/officer/analytics", params={"trend_days": 7}, headers=auth_headers(ctx["pune_officer"])
    )

    assert response.status_code == 200
    trend = response.json()["complaint_trend"]
    today = datetime.now(timezone.utc).date().isoformat()
    assert any(point["date"] == today for point in trend)


def test_non_officer_cannot_access_officer_analytics(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)

    response = client.get("/api/v1/officer/analytics", headers=auth_headers(ctx["inspector1_profile"].user))

    assert response.status_code == 403


def test_unauthenticated_cannot_access_officer_analytics(client: TestClient) -> None:
    response = client.get("/api/v1/officer/analytics")

    assert response.status_code == 401
