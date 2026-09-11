"""Legal action tracking service.

Officers record legal actions (fines, licence actions, prosecutions) against
businesses when a complaint reaches LEGAL_ACTION_IN_PROGRESS status. Concluding
an action automatically resolves the complaint.
"""
import uuid

from sqlalchemy.orm import Session

from app.models.complaint import Complaint
from app.models.legal_action import LegalAction
from app.models.staff_profile import StaffProfile
from app.repositories import audit_log_repository, legal_action_repository
from app.schemas.legal_action import (
    LegalActionCreateRequest,
    LegalActionRead,
    LegalActionUpdateRequest,
)
from app.services import complaint_service
from app.utils.enums import ComplaintStatus, LegalActionStatus
from app.utils.exceptions import ConflictError, NotFoundError, PermissionDeniedError


def create_legal_action(
    db: Session,
    officer: StaffProfile,
    complaint: Complaint,
    payload: LegalActionCreateRequest,
) -> LegalAction:
    if complaint.status != ComplaintStatus.LEGAL_ACTION_IN_PROGRESS:
        raise ConflictError(
            "Legal actions can only be created when the complaint status is 'legal_action_in_progress'."
        )

    action = legal_action_repository.create(
        db,
        complaint_id=complaint.id,
        lab_test_result_id=payload.lab_test_result_id,
        initiated_by_id=officer.id,
        fss_act_section=payload.fss_act_section,
        action_type=payload.action_type,
        fine_amount=payload.fine_amount,
        case_reference=payload.case_reference,
        court_or_tribunal=payload.court_or_tribunal,
        status=LegalActionStatus.INITIATED,
    )

    audit_log_repository.record(
        db,
        actor_user_id=officer.user_id,
        action="legal_action_created",
        entity_type="legal_action",
        entity_id=action.id,
        details={"action_type": payload.action_type.value, "complaint_id": str(complaint.id)},
    )
    db.commit()
    return legal_action_repository.get_by_id(db, action.id)


def update_legal_action(
    db: Session,
    officer: StaffProfile,
    action_id: uuid.UUID,
    payload: LegalActionUpdateRequest,
) -> LegalAction:
    action = legal_action_repository.get_by_id(db, action_id)
    if action is None:
        raise NotFoundError("Legal action not found.")
    # Scope check: complaint must belong to officer's district
    if action.complaint.district_id != officer.district_id:
        raise PermissionDeniedError()
    if action.status == LegalActionStatus.CONCLUDED:
        raise ConflictError("This legal action is already concluded.")

    if payload.status is not None:
        action.status = payload.status
    if payload.outcome_notes is not None:
        action.outcome_notes = payload.outcome_notes
    if payload.case_reference is not None:
        action.case_reference = payload.case_reference
    if payload.court_or_tribunal is not None:
        action.court_or_tribunal = payload.court_or_tribunal
    db.flush()

    if action.status == LegalActionStatus.CONCLUDED:
        complaint_service.apply_system_transition(
            db, action.complaint, ComplaintStatus.RESOLVED, officer.user_id,
            reason=f"Legal action concluded: {action.outcome_notes or ''}".strip(": "),
        )

    audit_log_repository.record(
        db,
        actor_user_id=officer.user_id,
        action="legal_action_updated",
        entity_type="legal_action",
        entity_id=action.id,
        details={"new_status": payload.status.value if payload.status else None},
    )
    db.commit()
    return legal_action_repository.get_by_id(db, action.id)


def list_for_complaint(db: Session, complaint_id: uuid.UUID) -> list[LegalAction]:
    return legal_action_repository.list_by_complaint(db, complaint_id)


def to_legal_action_read(action: LegalAction) -> LegalActionRead:
    return LegalActionRead(
        id=action.id,
        complaint_id=action.complaint_id,
        lab_test_result_id=action.lab_test_result_id,
        initiated_by_id=action.initiated_by_id,
        initiated_by_name=action.initiated_by.user.full_name,
        fss_act_section=action.fss_act_section,
        action_type=action.action_type,
        fine_amount=action.fine_amount,
        case_reference=action.case_reference,
        court_or_tribunal=action.court_or_tribunal,
        status=action.status,
        outcome_notes=action.outcome_notes,
        created_at=action.created_at,
        updated_at=action.updated_at,
    )