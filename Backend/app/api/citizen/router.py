import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_citizen
from app.models.user import User
from app.schemas.complaint import ComplaintCreateRequest, ComplaintRead, PaginatedComplaints
from app.schemas.complaint_status_history import ComplaintStatusHistoryRead
from app.schemas.evidence import EvidenceRead
from app.repositories import complaint_status_history_repository
from app.services import complaint_service, evidence_service
from app.utils.enums import ComplaintStatus

router = APIRouter(prefix="/complaints", tags=["citizen-complaints"], dependencies=[Depends(require_citizen)])


@router.post("", response_model=ComplaintRead, status_code=status.HTTP_201_CREATED)
def create_complaint(
    payload: ComplaintCreateRequest,
    current_user: User = Depends(require_citizen),
    db: Session = Depends(get_db),
) -> ComplaintRead:
    complaint = complaint_service.create_complaint(db, current_user, payload)
    return complaint_service.to_complaint_read(complaint)


@router.get("/my", response_model=PaginatedComplaints)
def list_my_complaints(
    status_filter: ComplaintStatus | None = Query(default=None, alias="status"),
    category_id: uuid.UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_citizen),
    db: Session = Depends(get_db),
) -> PaginatedComplaints:
    items, total = complaint_service.list_for_citizen(
        db,
        current_user.id,
        status=status_filter,
        category_id=category_id,
        page=page,
        page_size=page_size,
    )
    return PaginatedComplaints(
        items=[complaint_service.to_complaint_summary(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{complaint_id}", response_model=ComplaintRead)
def get_complaint(
    complaint_id: uuid.UUID,
    current_user: User = Depends(require_citizen),
    db: Session = Depends(get_db),
) -> ComplaintRead:
    complaint = complaint_service.get_complaint_for_citizen(db, current_user.id, complaint_id)
    return complaint_service.to_complaint_read(complaint)


@router.get("/{complaint_id}/timeline", response_model=list[ComplaintStatusHistoryRead])
def get_timeline(
    complaint_id: uuid.UUID,
    current_user: User = Depends(require_citizen),
    db: Session = Depends(get_db),
) -> list[ComplaintStatusHistoryRead]:
    complaint = complaint_service.get_complaint_for_citizen(db, current_user.id, complaint_id)
    history = complaint_status_history_repository.list_by_complaint(db, complaint.id)
    return complaint_service.to_timeline_read(history)


@router.post("/{complaint_id}/evidence", response_model=EvidenceRead, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    complaint_id: uuid.UUID,
    file: UploadFile = File(...),
    captured_at: datetime | None = Form(default=None),
    latitude: float | None = Form(default=None),
    longitude: float | None = Form(default=None),
    current_user: User = Depends(require_citizen),
    db: Session = Depends(get_db),
) -> EvidenceRead:
    complaint = complaint_service.get_complaint_for_citizen(db, current_user.id, complaint_id)
    file_bytes = await file.read()
    evidence = evidence_service.upload_evidence(
        db,
        complaint=complaint,
        uploaded_by_user_id=current_user.id,
        file_bytes=file_bytes,
        filename=file.filename or "upload",
        content_type=file.content_type or "application/octet-stream",
        captured_at=captured_at,
        latitude=latitude,
        longitude=longitude,
    )
    return evidence_service.to_evidence_read(evidence)


@router.get("/{complaint_id}/evidence", response_model=list[EvidenceRead])
def list_evidence(
    complaint_id: uuid.UUID,
    current_user: User = Depends(require_citizen),
    db: Session = Depends(get_db),
) -> list[EvidenceRead]:
    complaint = complaint_service.get_complaint_for_citizen(db, current_user.id, complaint_id)
    return evidence_service.list_evidence_with_urls(db, complaint.id)
