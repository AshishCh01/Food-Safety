import uuid
from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.complaint import Complaint
from app.models.staff_profile import StaffProfile
from app.repositories import assignment_repository, audit_log_repository, notification_repository, staff_repository
from app.schemas.assignment import AssignmentRead, AssignmentSummary
from app.services import complaint_service
from app.utils.enums import ComplaintStatus, NotificationType, UserRole
from app.utils.exceptions import AssignmentNotFoundError, InvalidAssignmentError, NotFoundError


def assign_inspector(
    db: Session,
    officer: StaffProfile,
    complaint: Complaint,
    *,
    inspector_staff_id: uuid.UUID,
    due_at: datetime | None,
    notes: str | None,
) -> Assignment:
    if complaint.status != ComplaintStatus.VERIFIED:
        raise InvalidAssignmentError("Only verified complaints can be assigned to an inspector.")

    inspector = staff_repository.get_by_id(db, inspector_staff_id)
    if (
        inspector is None
        or inspector.role != UserRole.INSPECTOR
        or not inspector.is_active
        or inspector.district_id != officer.district_id
    ):
        raise NotFoundError("Inspector was not found in your district.")

    try:
        assignment = assignment_repository.create(
            db,
            complaint_id=complaint.id,
            assigned_to_staff_id=inspector.id,
            assigned_by_staff_id=officer.id,
            due_at=due_at,
            notes=notes,
        )
    except IntegrityError as exc:
        # Two concurrent assign-inspector requests for the same complaint
        # both passed the VERIFIED check above before either committed; the
        # database's unique constraint on assignments.complaint_id is the
        # actual source of truth here (see the migration that added it).
        db.rollback()
        raise InvalidAssignmentError("This complaint has already been assigned to an inspector.") from exc

    audit_log_repository.record(
        db,
        actor_user_id=officer.user_id,
        action="inspector_assigned",
        entity_type="assignment",
        entity_id=assignment.id,
        details={"complaint_id": str(complaint.id), "inspector_staff_id": str(inspector.id)},
    )

    notification_repository.create(
        db,
        user_id=inspector.user_id,
        type=NotificationType.INSPECTOR_ASSIGNED,
        title="New Case Assigned",
        message=f"You have been assigned to inspect complaint {complaint.complaint_number}.",
        entity_type="complaint",
        entity_id=complaint.id,
    )

    complaint_service.apply_system_transition(
        db,
        complaint,
        ComplaintStatus.ASSIGNED,
        officer.user_id,
        reason=f"Assigned to inspector {inspector.user.full_name}.",
    )

    return assignment_repository.get_by_id(db, assignment.id)


def get_assignment_for_inspector(db: Session, inspector_staff_id: uuid.UUID, assignment_id: uuid.UUID) -> Assignment:
    assignment = assignment_repository.get_by_id(db, assignment_id)
    if assignment is None or assignment.assigned_to_staff_id != inspector_staff_id:
        raise AssignmentNotFoundError()
    return assignment


def get_assignment_for_officer(db: Session, staff: StaffProfile, complaint: Complaint) -> Assignment:
    assignment = assignment_repository.get_by_complaint_id(db, complaint.id)
    if assignment is None or complaint.district_id != staff.district_id:
        raise AssignmentNotFoundError()
    return assignment


def list_for_inspector(
    db: Session,
    inspector_staff_id: uuid.UUID,
    *,
    status,
    page: int,
    page_size: int,
) -> tuple[list[Assignment], int]:
    return assignment_repository.list_by_inspector(
        db, inspector_staff_id, status=status, page=page, page_size=page_size
    )


def to_assignment_summary(assignment: Assignment) -> AssignmentSummary:
    return AssignmentSummary(
        id=assignment.id,
        complaint_id=assignment.complaint_id,
        complaint_number=assignment.complaint.complaint_number,
        complaint_title=assignment.complaint.title,
        inspector_staff_id=assignment.assigned_to_staff_id,
        inspector_name=assignment.assigned_to.user.full_name,
        status=assignment.status,
        assigned_at=assignment.assigned_at,
        due_at=assignment.due_at,
    )


def to_assignment_read(assignment: Assignment, *, inspection_read=None) -> AssignmentRead:
    return AssignmentRead(
        **to_assignment_summary(assignment).model_dump(),
        assigned_by_staff_id=assignment.assigned_by_staff_id,
        officer_name=assignment.assigned_by.user.full_name,
        notes=assignment.notes,
        complaint=complaint_service.to_complaint_read(assignment.complaint),
        inspection=inspection_read,
    )
