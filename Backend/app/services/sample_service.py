"""Sample collection and lab testing service.

Covers the full lifecycle of a food sample from collection during an inspection
through dispatch to a food analyst, receipt at the lab, and final result
submission -- which drives the complaint status transition.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.inspection import Inspection
from app.models.lab_test_result import LabTestResult
from app.models.sample import Sample
from app.models.staff_profile import StaffProfile
from app.repositories import (
    audit_log_repository,
    lab_test_result_repository,
    notification_repository,
    sample_repository,
    sample_sequence_repository,
    staff_repository,
)
from app.schemas.sample import (
    LabTestResultCreateRequest,
    LabTestResultRead,
    SampleCreateRequest,
    SampleDispatchRequest,
    SampleRead,
)
from app.services import complaint_service
from app.utils.enums import (
    LAB_UNSAFE_VERDICTS,
    ComplaintStatus,
    NotificationType,
    SampleStatus,
    UserRole,
)
from app.utils.exceptions import ConflictError, NotFoundError, PermissionDeniedError


# ---------------------------------------------------------------------------
# Sample lifecycle
# ---------------------------------------------------------------------------

def collect_sample(
    db: Session,
    inspector: StaffProfile,
    inspection: Inspection,
    payload: SampleCreateRequest,
) -> Sample:
    if inspection.inspector_id != inspector.id:
        raise PermissionDeniedError()

    now = datetime.now(timezone.utc)
    year = now.year
    seq = sample_sequence_repository.next_sequence_number(db, year)
    sample_code = f"SMP-{year}-{seq:06d}"

    sample = sample_repository.create(
        db,
        sample_code=sample_code,
        inspection_id=inspection.id,
        item_description=payload.item_description,
        quantity=payload.quantity,
        unit=payload.unit,
        seal_number=payload.seal_number,
        collected_by_id=inspector.id,
        collected_at=now,
        status=SampleStatus.COLLECTED,
    )

    audit_log_repository.record(
        db,
        actor_user_id=inspector.user_id,
        action="sample_collected",
        entity_type="sample",
        entity_id=sample.id,
        details={"sample_code": sample_code, "inspection_id": str(inspection.id)},
    )
    db.commit()
    return sample_repository.get_by_id(db, sample.id)


def dispatch_sample(
    db: Session,
    inspector: StaffProfile,
    sample: Sample,
    payload: SampleDispatchRequest,
) -> Sample:
    inspection = sample.inspection
    if inspection.inspector_id != inspector.id:
        raise PermissionDeniedError()
    if sample.status != SampleStatus.COLLECTED:
        raise ConflictError("Sample must be in COLLECTED status to dispatch.")

    if payload.food_analyst_id is not None:
        analyst = staff_repository.get_by_id(db, payload.food_analyst_id)
        if analyst is None or analyst.role != UserRole.FOOD_ANALYST or not analyst.is_active:
            raise NotFoundError("Food analyst not found or inactive.")
        sample.dispatched_to_id = payload.food_analyst_id
        sample.lab_name = None
    else:
        sample.dispatched_to_id = None
        sample.lab_name = payload.lab_name

    sample.status = SampleStatus.DISPATCHED
    sample.dispatched_at = datetime.now(timezone.utc)
    db.flush()

    audit_log_repository.record(
        db,
        actor_user_id=inspector.user_id,
        action="sample_dispatched",
        entity_type="sample",
        entity_id=sample.id,
        details={
            "food_analyst_id": str(payload.food_analyst_id) if payload.food_analyst_id else None,
            "lab_name": payload.lab_name,
        },
    )
    db.commit()
    return sample_repository.get_by_id(db, sample.id)


def receive_sample(db: Session, analyst: StaffProfile, sample: Sample) -> Sample:
    if sample.dispatched_to_id != analyst.id:
        raise PermissionDeniedError("This sample was not dispatched to you.")
    if sample.status != SampleStatus.DISPATCHED:
        raise ConflictError("Sample must be in DISPATCHED status to mark received.")

    sample.status = SampleStatus.RECEIVED_AT_LAB
    db.flush()

    audit_log_repository.record(
        db,
        actor_user_id=analyst.user_id,
        action="sample_received_at_lab",
        entity_type="sample",
        entity_id=sample.id,
        details={},
    )
    db.commit()
    return sample_repository.get_by_id(db, sample.id)


def submit_result(
    db: Session,
    analyst: StaffProfile,
    sample: Sample,
    payload: LabTestResultCreateRequest,
    report_storage_path: str | None = None,
) -> LabTestResult:
    if sample.dispatched_to_id != analyst.id:
        raise PermissionDeniedError("This sample was not dispatched to you.")
    if sample.status not in (SampleStatus.RECEIVED_AT_LAB, SampleStatus.TESTING_IN_PROGRESS):
        raise ConflictError("Sample must be received at lab before submitting a result.")
    if lab_test_result_repository.get_by_sample_id(db, sample.id) is not None:
        raise ConflictError("A result has already been submitted for this sample.")

    result = lab_test_result_repository.create(
        db,
        sample_id=sample.id,
        food_analyst_id=analyst.id,
        tested_at=datetime.now(timezone.utc),
        report_storage_path=report_storage_path,
        verdict=payload.verdict,
        remarks=payload.remarks,
    )

    sample.status = SampleStatus.RESULT_RECEIVED
    db.flush()

    # Drive complaint status based on verdict
    complaint = sample.inspection.complaint
    if payload.verdict in LAB_UNSAFE_VERDICTS:
        new_status = ComplaintStatus.LEGAL_ACTION_IN_PROGRESS
        citizen_title = "Lab Result: Action Required"
        citizen_msg = (
            f"The lab result for a sample taken from complaint {complaint.complaint_number} "
            f"indicates {payload.verdict.value}. Legal action proceedings have been initiated."
        )
    else:
        new_status = ComplaintStatus.ACTION_IN_PROGRESS
        citizen_title = "Lab Result: Sample Safe"
        citizen_msg = (
            f"The lab result for a sample from complaint {complaint.complaint_number} "
            "shows no safety issues. The complaint is now under action review."
        )

    complaint_service.apply_system_transition(
        db, complaint, new_status, analyst.user_id,
        reason=f"Lab result submitted: {payload.verdict.value}."
    )

    # Notify citizen
    notification_repository.create(
        db,
        user_id=complaint.submitted_by_user_id,
        type=NotificationType.SAMPLE_RESULT_RECEIVED,
        title=citizen_title,
        message=citizen_msg,
        entity_type="complaint",
        entity_id=complaint.id,
    )

    audit_log_repository.record(
        db,
        actor_user_id=analyst.user_id,
        action="lab_result_submitted",
        entity_type="sample",
        entity_id=sample.id,
        details={"verdict": payload.verdict.value},
    )
    # commit already called inside apply_system_transition
    return result


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

def get_sample_for_inspector(db: Session, inspector_id, sample_id) -> Sample:
    sample = sample_repository.get_by_id(db, sample_id)
    if sample is None or sample.inspection.inspector_id != inspector_id:
        raise NotFoundError("Sample not found.")
    return sample


def get_sample_for_analyst(db: Session, analyst_id, sample_id) -> Sample:
    sample = sample_repository.get_by_id(db, sample_id)
    if sample is None or sample.dispatched_to_id != analyst_id:
        raise NotFoundError("Sample not found.")
    return sample


def list_for_inspection(db: Session, inspection_id) -> list[Sample]:
    return sample_repository.list_by_inspection(db, inspection_id)


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def _to_result_read(result: LabTestResult) -> LabTestResultRead:
    return LabTestResultRead(
        id=result.id,
        sample_id=result.sample_id,
        food_analyst_id=result.food_analyst_id,
        food_analyst_name=result.food_analyst.user.full_name,
        tested_at=result.tested_at,
        report_storage_path=result.report_storage_path,
        verdict=result.verdict,
        remarks=result.remarks,
        created_at=result.created_at,
    )


def to_sample_read(sample: Sample) -> SampleRead:
    return SampleRead(
        id=sample.id,
        sample_code=sample.sample_code,
        inspection_id=sample.inspection_id,
        item_description=sample.item_description,
        quantity=sample.quantity,
        unit=sample.unit,
        seal_number=sample.seal_number,
        collected_by_id=sample.collected_by_id,
        collected_by_name=sample.collected_by.user.full_name,
        collected_at=sample.collected_at,
        status=sample.status,
        dispatched_to_id=sample.dispatched_to_id,
        dispatched_to_name=sample.dispatched_to.user.full_name if sample.dispatched_to else None,
        dispatched_at=sample.dispatched_at,
        lab_name=sample.lab_name,
        lab_test_result=_to_result_read(sample.lab_test_result) if sample.lab_test_result else None,
        created_at=sample.created_at,
        updated_at=sample.updated_at,
    )