import pytest
from sqlalchemy.orm import Session

from app.schemas.inspection import InspectionCompleteRequest, InspectionUpdateRequest
from app.services import assignment_service, inspection_service
from app.tests.factories import (
    create_assignment,
    create_complaint,
    create_complaint_category,
    create_district,
    create_division,
    create_inspection,
    create_staff,
    create_user,
)
from app.utils.enums import ComplaintStatus, InspectionStatus, UserRole
from app.utils.exceptions import ConflictError, InspectionNotFoundError, InvalidAssignmentError


def _base_setup(db_session: Session, *, complaint_status=ComplaintStatus.ASSIGNED):
    division = create_division(db_session, name="Pune Division", code="PUN")
    district = create_district(db_session, division, name="Pune", code="PUN")
    officer, officer_profile = create_staff(
        db_session, district, role=UserRole.DISTRICT_OFFICER, email="officer@example.com", employee_code="DO-1"
    )
    inspector, inspector_profile = create_staff(
        db_session, district, role=UserRole.INSPECTOR, email="inspector@example.com", employee_code="INS-1"
    )
    other_inspector, other_inspector_profile = create_staff(
        db_session, district, role=UserRole.INSPECTOR, email="other@example.com", employee_code="INS-2"
    )
    category = create_complaint_category(db_session)
    citizen = create_user(db_session, email="citizen@example.com")
    complaint = create_complaint(db_session, citizen, district, category, status=complaint_status)
    return {
        "district": district,
        "officer_profile": officer_profile,
        "inspector_profile": inspector_profile,
        "other_inspector_profile": other_inspector_profile,
        "complaint": complaint,
    }


def test_assign_inspector_requires_verified_complaint(db_session: Session) -> None:
    ctx = _base_setup(db_session, complaint_status=ComplaintStatus.SUBMITTED)

    with pytest.raises(InvalidAssignmentError):
        assignment_service.assign_inspector(
            db_session,
            ctx["officer_profile"],
            ctx["complaint"],
            inspector_staff_id=ctx["inspector_profile"].id,
            due_at=None,
            notes=None,
        )


def test_assign_inspector_moves_complaint_to_assigned(db_session: Session) -> None:
    ctx = _base_setup(db_session, complaint_status=ComplaintStatus.VERIFIED)

    assignment_service.assign_inspector(
        db_session,
        ctx["officer_profile"],
        ctx["complaint"],
        inspector_staff_id=ctx["inspector_profile"].id,
        due_at=None,
        notes=None,
    )

    assert ctx["complaint"].status == ComplaintStatus.ASSIGNED


def test_get_inspection_for_inspector_masks_other_inspectors(db_session: Session) -> None:
    ctx = _base_setup(db_session)
    create_assignment(db_session, ctx["complaint"], ctx["inspector_profile"], ctx["officer_profile"])
    inspection = create_inspection(db_session, ctx["complaint"], ctx["inspector_profile"])

    with pytest.raises(InspectionNotFoundError):
        inspection_service.get_inspection_for_inspector(db_session, ctx["other_inspector_profile"].id, inspection.id)

    found = inspection_service.get_inspection_for_inspector(
        db_session, ctx["inspector_profile"].id, inspection.id
    )
    assert found.id == inspection.id


def test_starting_an_already_started_inspection_conflicts(db_session: Session) -> None:
    ctx = _base_setup(db_session)
    create_assignment(db_session, ctx["complaint"], ctx["inspector_profile"], ctx["officer_profile"])
    inspection = create_inspection(db_session, ctx["complaint"], ctx["inspector_profile"])

    inspection_service.update_inspection(
        db_session, ctx["inspector_profile"], inspection, InspectionUpdateRequest(status="in_progress")
    )
    assert inspection.inspection_status == InspectionStatus.IN_PROGRESS

    with pytest.raises(ConflictError):
        inspection_service.update_inspection(
            db_session, ctx["inspector_profile"], inspection, InspectionUpdateRequest(status="in_progress")
        )


def test_complete_before_starting_conflicts(db_session: Session) -> None:
    ctx = _base_setup(db_session)
    create_assignment(db_session, ctx["complaint"], ctx["inspector_profile"], ctx["officer_profile"])
    inspection = create_inspection(db_session, ctx["complaint"], ctx["inspector_profile"])

    with pytest.raises(ConflictError):
        inspection_service.complete_inspection(
            db_session,
            ctx["inspector_profile"],
            inspection,
            InspectionCompleteRequest(summary="Done.", action_recommended="None."),
        )
