from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.complaint import Complaint
from app.models.inspection import Inspection
from app.models.inspection_finding import InspectionFinding
from app.models.staff_profile import StaffProfile
from app.repositories import (
    assignment_repository,
    audit_log_repository,
    inspection_finding_repository,
    inspection_repository,
)
from app.schemas.inspection import (
    InspectionCompleteRequest,
    InspectionCreateRequest,
    InspectionFindingCreateRequest,
    InspectionFindingRead,
    InspectionRead,
    InspectionSummary,
    InspectionUpdateRequest,
)
from app.services import complaint_service
from app.utils.enums import AssignmentStatus, ComplaintStatus, InspectionStatus
from app.utils.exceptions import ConflictError, InspectionNotFoundError


def create_inspection(db: Session, inspector: StaffProfile, payload: InspectionCreateRequest) -> Inspection:
    assignment = assignment_repository.get_by_complaint_id(db, payload.complaint_id)
    if assignment is None or assignment.assigned_to_staff_id != inspector.id:
        raise InspectionNotFoundError("No assignment was found for this complaint.")

    complaint = assignment.complaint
    if complaint.status != ComplaintStatus.ASSIGNED:
        raise ConflictError("This complaint is not awaiting inspection.")
    if inspection_repository.get_by_complaint_id(db, complaint.id) is not None:
        raise ConflictError("An inspection already exists for this complaint.")

    inspection = Inspection(complaint_id=complaint.id, inspector_id=inspector.id, scheduled_at=payload.scheduled_at)
    inspection_repository.create(db, inspection)

    audit_log_repository.record(
        db,
        actor_user_id=inspector.user_id,
        action="inspection_created",
        entity_type="inspection",
        entity_id=inspection.id,
        details={"complaint_id": str(complaint.id)},
    )

    complaint_service.apply_system_transition(
        db, complaint, ComplaintStatus.INSPECTION_SCHEDULED, inspector.user_id, reason="Inspection scheduled."
    )

    return inspection_repository.get_by_id(db, inspection.id)


def get_inspection_for_inspector(db: Session, inspector_staff_id, inspection_id) -> Inspection:
    inspection = inspection_repository.get_by_id(db, inspection_id)
    if inspection is None or inspection.inspector_id != inspector_staff_id:
        raise InspectionNotFoundError()
    return inspection


def get_inspection_for_complaint_if_owned(db: Session, inspector_staff_id, complaint_id) -> Inspection | None:
    inspection = inspection_repository.get_by_complaint_id(db, complaint_id)
    if inspection is None or inspection.inspector_id != inspector_staff_id:
        return None
    return inspection


def get_inspection_for_officer(db: Session, staff: StaffProfile, complaint: Complaint) -> Inspection:
    inspection = inspection_repository.get_by_complaint_id(db, complaint.id)
    if inspection is None or complaint.district_id != staff.district_id:
        raise InspectionNotFoundError()
    return inspection


def _start_inspection(db: Session, inspector: StaffProfile, inspection: Inspection) -> None:
    if inspection.inspection_status != InspectionStatus.SCHEDULED:
        raise ConflictError("Inspection must be scheduled before it can be started.")

    inspection.inspection_status = InspectionStatus.IN_PROGRESS
    inspection.started_at = datetime.now(timezone.utc)
    db.flush()

    assignment = assignment_repository.get_by_complaint_id(db, inspection.complaint_id)
    assignment.status = AssignmentStatus.IN_PROGRESS
    db.flush()

    complaint_service.apply_system_transition(
        db, inspection.complaint, ComplaintStatus.UNDER_INSPECTION, inspector.user_id, reason="Inspection started."
    )


def update_inspection(
    db: Session, inspector: StaffProfile, inspection: Inspection, payload: InspectionUpdateRequest
) -> Inspection:
    if inspection.inspector_id != inspector.id:
        raise InspectionNotFoundError()
    if inspection.inspection_status == InspectionStatus.COMPLETED:
        raise ConflictError("This inspection has already been completed.")

    if payload.scheduled_at is not None:
        inspection.scheduled_at = payload.scheduled_at
    if payload.summary is not None:
        inspection.summary = payload.summary
    if payload.action_recommended is not None:
        inspection.action_recommended = payload.action_recommended
    db.flush()

    if payload.status == "in_progress":
        _start_inspection(db, inspector, inspection)
    else:
        db.commit()

    return inspection_repository.get_by_id(db, inspection.id)


def add_finding(
    db: Session, inspector: StaffProfile, inspection: Inspection, payload: InspectionFindingCreateRequest
) -> InspectionFinding:
    if inspection.inspector_id != inspector.id:
        raise InspectionNotFoundError()
    if inspection.inspection_status == InspectionStatus.COMPLETED:
        raise ConflictError("Cannot add findings to a completed inspection.")

    finding = inspection_finding_repository.create(
        db,
        inspection_id=inspection.id,
        check_code=payload.check_code,
        finding=payload.finding,
        severity=payload.severity,
        compliant=payload.compliant,
        notes=payload.notes,
        corrective_action=payload.corrective_action,
    )

    audit_log_repository.record(
        db,
        actor_user_id=inspector.user_id,
        action="inspection_finding_added",
        entity_type="inspection",
        entity_id=inspection.id,
        details={"check_code": payload.check_code, "compliant": payload.compliant},
    )

    db.commit()
    db.refresh(finding)
    return finding


def complete_inspection(
    db: Session, inspector: StaffProfile, inspection: Inspection, payload: InspectionCompleteRequest
) -> Inspection:
    if inspection.inspector_id != inspector.id:
        raise InspectionNotFoundError()
    if inspection.inspection_status != InspectionStatus.IN_PROGRESS:
        raise ConflictError("Inspection must be in progress before it can be completed.")

    inspection.inspection_status = InspectionStatus.COMPLETED
    inspection.completed_at = datetime.now(timezone.utc)
    inspection.summary = payload.summary
    inspection.action_recommended = payload.action_recommended
    db.flush()

    assignment = assignment_repository.get_by_complaint_id(db, inspection.complaint_id)
    assignment.status = AssignmentStatus.COMPLETED
    db.flush()

    audit_log_repository.record(
        db,
        actor_user_id=inspector.user_id,
        action="inspection_completed",
        entity_type="inspection",
        entity_id=inspection.id,
        details={"action_recommended": payload.action_recommended},
    )

    complaint_service.apply_system_transition(
        db,
        inspection.complaint,
        ComplaintStatus.INSPECTION_COMPLETED,
        inspector.user_id,
        reason="Inspection completed.",
    )

    return inspection_repository.get_by_id(db, inspection.id)


def list_for_inspector(db: Session, inspector_staff_id, *, status, page: int, page_size: int):
    return inspection_repository.list_by_inspector(
        db, inspector_staff_id, status=status, page=page, page_size=page_size
    )


def to_finding_read(finding: InspectionFinding) -> InspectionFindingRead:
    return InspectionFindingRead(
        id=finding.id,
        inspection_id=finding.inspection_id,
        check_code=finding.check_code,
        finding=finding.finding,
        severity=finding.severity,
        compliant=finding.compliant,
        notes=finding.notes,
        corrective_action=finding.corrective_action,
        created_at=finding.created_at,
    )


def to_inspection_read(inspection: Inspection) -> InspectionRead:
    return InspectionRead(
        id=inspection.id,
        complaint_id=inspection.complaint_id,
        complaint_number=inspection.complaint.complaint_number,
        inspector_staff_id=inspection.inspector_id,
        inspector_name=inspection.inspector.user.full_name,
        scheduled_at=inspection.scheduled_at,
        started_at=inspection.started_at,
        completed_at=inspection.completed_at,
        inspection_status=inspection.inspection_status,
        summary=inspection.summary,
        action_recommended=inspection.action_recommended,
        findings=[to_finding_read(finding) for finding in inspection.findings],
        created_at=inspection.created_at,
        updated_at=inspection.updated_at,
    )


def to_inspection_summary(inspection: Inspection) -> InspectionSummary:
    return InspectionSummary(
        id=inspection.id,
        complaint_id=inspection.complaint_id,
        complaint_number=inspection.complaint.complaint_number,
        inspection_status=inspection.inspection_status,
        scheduled_at=inspection.scheduled_at,
        completed_at=inspection.completed_at,
    )
