import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_staff_profile, require_food_analyst
from app.models.staff_profile import StaffProfile
from app.schemas.sample import LabTestResultCreateRequest, LabTestResultRead, PaginatedSamples, SampleRead
from app.services import sample_service
from app.utils.enums import SampleStatus

router = APIRouter(prefix="/food-analyst", tags=["food-analyst"], dependencies=[Depends(require_food_analyst)])


@router.get("/samples", response_model=PaginatedSamples)
def list_samples(
    status_filter: SampleStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
):
    from app.repositories import sample_repository

    items, total = sample_repository.list_for_analyst(
        db, staff.id, status=status_filter, page=page, page_size=page_size
    )
    return PaginatedSamples(
        items=[sample_service.to_sample_read(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/samples/{sample_id}/receive", response_model=SampleRead)
def receive_sample(
    sample_id: uuid.UUID,
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
):
    sample = sample_service.get_sample_for_analyst(db, staff.id, sample_id)
    received = sample_service.receive_sample(db, staff, sample)
    return sample_service.to_sample_read(received)


@router.post("/samples/{sample_id}/result", response_model=LabTestResultRead)
def submit_result(
    sample_id: uuid.UUID,
    payload: LabTestResultCreateRequest,
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
):
    sample = sample_service.get_sample_for_analyst(db, staff.id, sample_id)
    # File upload handling would go here in a real implementation (multipart form data).
    # Since this relies on a separate storage_service function that takes bytes,
    # we'll mock the storage path for the JSON payload for now.
    result = sample_service.submit_result(db, staff, sample, payload, report_storage_path=None)
    
    # We must construct a LabTestResultRead directly since it's nested in the sample read.
    return LabTestResultRead(
        id=result.id,
        sample_id=result.sample_id,
        food_analyst_id=result.food_analyst_id,
        food_analyst_name=staff.user.full_name,
        tested_at=result.tested_at,
        report_storage_path=result.report_storage_path,
        verdict=result.verdict,
        remarks=result.remarks,
        created_at=result.created_at,
    )