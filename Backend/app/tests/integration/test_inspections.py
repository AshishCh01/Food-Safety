from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services import storage_service
from app.tests.factories import (
    auth_headers,
    create_assignment,
    create_complaint,
    create_complaint_category,
    create_district,
    create_division,
    create_inspection,
    create_staff,
    create_user,
)
from app.utils.enums import AssignmentStatus, ComplaintStatus, InspectionStatus, UserRole


def _setup(db_session: Session):
    division = create_division(db_session, name="Pune Division", code="PUN")
    pune = create_district(db_session, division, name="Pune", code="PUN")
    nagpur = create_district(db_session, division, name="Nagpur", code="NGP")

    officer, officer_profile = create_staff(
        db_session, pune, role=UserRole.DISTRICT_OFFICER, email="officer@example.com", employee_code="DO-1"
    )
    inspector, inspector_profile = create_staff(
        db_session, pune, role=UserRole.INSPECTOR, email="inspector@example.com", employee_code="INS-1"
    )
    other_inspector, other_inspector_profile = create_staff(
        db_session, nagpur, role=UserRole.INSPECTOR, email="other.inspector@example.com", employee_code="INS-2"
    )

    category = create_complaint_category(db_session)
    citizen = create_user(db_session, email="citizen@example.com")
    complaint = create_complaint(db_session, citizen, pune, category, status=ComplaintStatus.ASSIGNED)
    create_assignment(db_session, complaint, inspector_profile, officer_profile)

    return {
        "officer": officer,
        "officer_profile": officer_profile,
        "inspector": inspector,
        "inspector_profile": inspector_profile,
        "other_inspector": other_inspector,
        "complaint": complaint,
    }


def test_inspector_creates_inspection(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)

    response = client.post(
        "/api/v1/inspector/inspections",
        json={"complaint_id": str(ctx["complaint"].id)},
        headers=auth_headers(ctx["inspector"]),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["inspection_status"] == "scheduled"
    assert body["complaint_id"] == str(ctx["complaint"].id)


def test_unassigned_inspector_cannot_create_inspection(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)

    response = client.post(
        "/api/v1/inspector/inspections",
        json={"complaint_id": str(ctx["complaint"].id)},
        headers=auth_headers(ctx["other_inspector"]),
    )

    assert response.status_code == 404


def test_cannot_create_second_inspection_for_same_complaint(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)
    payload = {"complaint_id": str(ctx["complaint"].id)}

    first = client.post("/api/v1/inspector/inspections", json=payload, headers=auth_headers(ctx["inspector"]))
    assert first.status_code == 201

    second = client.post("/api/v1/inspector/inspections", json=payload, headers=auth_headers(ctx["inspector"]))
    assert second.status_code == 409


def test_start_inspection_transitions_complaint_and_assignment(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)
    inspection = create_inspection(db_session, ctx["complaint"], ctx["inspector_profile"])

    response = client.patch(
        f"/api/v1/inspector/inspections/{inspection.id}",
        json={"status": "in_progress"},
        headers=auth_headers(ctx["inspector"]),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["inspection_status"] == "in_progress"
    assert body["started_at"] is not None

    complaint_check = client.get(
        f"/api/v1/officer/complaints/{ctx['complaint'].id}", headers=auth_headers(ctx["officer"])
    )
    assert complaint_check.json()["status"] == "under_inspection"


def test_add_finding(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)
    inspection = create_inspection(db_session, ctx["complaint"], ctx["inspector_profile"])

    response = client.post(
        f"/api/v1/inspector/inspections/{inspection.id}/findings",
        json={
            "check_code": "HYGIENE-01",
            "finding": "Food storage area was unclean.",
            "severity": "high",
            "compliant": False,
            "corrective_action": "Deep clean storage area within 48 hours.",
        },
        headers=auth_headers(ctx["inspector"]),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["check_code"] == "HYGIENE-01"
    assert body["compliant"] is False


def test_upload_inspection_evidence(client: TestClient, db_session: Session, monkeypatch) -> None:
    ctx = _setup(db_session)
    inspection = create_inspection(db_session, ctx["complaint"], ctx["inspector_profile"])
    monkeypatch.setattr(storage_service, "upload_file", lambda bucket, path, content, content_type: path)

    response = client.post(
        f"/api/v1/inspector/inspections/{inspection.id}/evidence",
        headers=auth_headers(ctx["inspector"]),
        files={"file": ("site.jpg", b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01fake-image-bytes", "image/jpeg")},
    )

    assert response.status_code == 201
    assert response.json()["file_name"] == "site.jpg"


def test_complete_requires_in_progress(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)
    inspection = create_inspection(db_session, ctx["complaint"], ctx["inspector_profile"])

    response = client.post(
        f"/api/v1/inspector/inspections/{inspection.id}/complete",
        json={"summary": "All checks passed.", "action_recommended": "No action required."},
        headers=auth_headers(ctx["inspector"]),
    )

    assert response.status_code == 409


def test_complete_inspection_happy_path(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)
    inspection = create_inspection(db_session, ctx["complaint"], ctx["inspector_profile"], status=InspectionStatus.IN_PROGRESS)

    response = client.post(
        f"/api/v1/inspector/inspections/{inspection.id}/complete",
        json={"summary": "Minor hygiene issues found.", "action_recommended": "Follow-up inspection in 30 days."},
        headers=auth_headers(ctx["inspector"]),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["inspection_status"] == "completed"
    assert body["completed_at"] is not None

    complaint_check = client.get(
        f"/api/v1/officer/complaints/{ctx['complaint'].id}", headers=auth_headers(ctx["officer"])
    )
    assert complaint_check.json()["status"] == "inspection_completed"


def test_findings_rejected_after_completion(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)
    inspection = create_inspection(db_session, ctx["complaint"], ctx["inspector_profile"], status=InspectionStatus.COMPLETED)

    response = client.post(
        f"/api/v1/inspector/inspections/{inspection.id}/findings",
        json={"check_code": "X", "finding": "late finding", "severity": "low", "compliant": True},
        headers=auth_headers(ctx["inspector"]),
    )

    assert response.status_code == 409


def test_officer_views_completed_inspection_with_findings(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)
    inspection = create_inspection(db_session, ctx["complaint"], ctx["inspector_profile"], status=InspectionStatus.IN_PROGRESS)
    client.post(
        f"/api/v1/inspector/inspections/{inspection.id}/findings",
        json={"check_code": "A1", "finding": "ok", "severity": "low", "compliant": True},
        headers=auth_headers(ctx["inspector"]),
    )
    client.post(
        f"/api/v1/inspector/inspections/{inspection.id}/complete",
        json={"summary": "Done.", "action_recommended": "None."},
        headers=auth_headers(ctx["inspector"]),
    )

    response = client.get(
        f"/api/v1/officer/complaints/{ctx['complaint'].id}/inspection", headers=auth_headers(ctx["officer"])
    )

    assert response.status_code == 200
    body = response.json()
    assert body["inspection_status"] == "completed"
    assert len(body["findings"]) == 1


def test_officer_can_resolve_after_inspection_completed(client: TestClient, db_session: Session) -> None:
    ctx = _setup(db_session)
    inspection = create_inspection(db_session, ctx["complaint"], ctx["inspector_profile"], status=InspectionStatus.IN_PROGRESS)
    client.post(
        f"/api/v1/inspector/inspections/{inspection.id}/complete",
        json={"summary": "Done.", "action_recommended": "None."},
        headers=auth_headers(ctx["inspector"]),
    )

    valid = client.patch(
        f"/api/v1/officer/complaints/{ctx['complaint'].id}/status",
        json={"status": "resolved"},
        headers=auth_headers(ctx["officer"]),
    )
    assert valid.status_code == 200
    assert valid.json()["status"] == "resolved"

    invalid = client.patch(
        f"/api/v1/officer/complaints/{ctx['complaint'].id}/status",
        json={"status": "submitted"},
        headers=auth_headers(ctx["officer"]),
    )
    assert invalid.status_code == 409
