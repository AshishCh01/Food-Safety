import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_staff_profile, require_district_officer
from app.models.staff_profile import StaffProfile
from app.repositories import complaint_status_history_repository, staff_repository
from app.schemas.assignment import AssignmentCreateRequest, AssignmentRead
from app.schemas.complaint import (
    ComplaintMapData,
    ComplaintRead,
    ComplaintStatusUpdateRequest,
    ComplaintSummary,
    PaginatedComplaints,
)
from app.schemas.complaint_status_history import ComplaintStatusHistoryRead
from app.schemas.evidence import EvidenceRead
from app.schemas.inspection import InspectionRead
from app.schemas.staff import StaffRead
from app.services import (
    assignment_service,
    complaint_service,
    evidence_service,
    inspection_service,
    staff_service,
)
from app.utils.enums import ComplaintPriority, ComplaintStatus, UserRole

router = APIRouter(prefix="/officer", tags=["officer"], dependencies=[Depends(require_district_officer)])


@router.get("/dashboard")
def dashboard(
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> dict:
    inspector_count = staff_repository.count_by_district_role(db, staff.district_id, UserRole.INSPECTOR)
    return {
        "district_id": staff.district_id,
        "district_name": staff.district.name,
        "district_code": staff.district.code,
        "officer_name": staff.user.full_name,
        "inspector_count": inspector_count,
    }


@router.get("/inspectors", response_model=list[StaffRead])
def list_inspectors(
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> list[StaffRead]:
    # District scope is derived only from the authenticated officer's own
    # staff profile, never from a client-supplied parameter, enforcing
    # server-side district isolation.
    inspectors = staff_repository.list_by_district(db, staff.district_id, role=UserRole.INSPECTOR)
    return [staff_service.to_staff_read(inspector) for inspector in inspectors]


@router.get("/complaints", response_model=PaginatedComplaints)
def list_complaints(
    status_filter: ComplaintStatus | None = Query(default=None, alias="status"),
    priority: ComplaintPriority | None = Query(default=None),
    category_id: uuid.UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> PaginatedComplaints:
    # District scope always comes from the authenticated officer's own staff
    # profile, never from a client-supplied parameter.
    items, total = complaint_service.list_for_district(
        db,
        staff.district_id,
        status=status_filter,
        priority=priority,
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


@router.get("/complaints/map", response_model=ComplaintMapData)
def get_complaints_map(
    min_lat: float | None = Query(default=None),
    min_lng: float | None = Query(default=None),
    max_lat: float | None = Query(default=None),
    max_lng: float | None = Query(default=None),
    status_filter: ComplaintStatus | None = Query(default=None, alias="status"),
    priority: ComplaintPriority | None = Query(default=None),
    category_id: uuid.UUID | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> ComplaintMapData:
    # District scope always comes from the authenticated officer's own staff
    # profile, never from a client-supplied parameter - the map can only
    # ever show the officer's own district.
    markers = complaint_service.list_map_markers_for_district(
        db,
        staff.district_id,
        min_lat=min_lat,
        min_lng=min_lng,
        max_lat=max_lat,
        max_lng=max_lng,
        status=status_filter,
        priority=priority,
        category_id=category_id,
        date_from=date_from,
        date_to=date_to,
    )
    return ComplaintMapData(
        items=[complaint_service.to_map_marker(item) for item in markers],
        total=len(markers),
    )


@router.get("/complaints/nearby", response_model=list[ComplaintSummary])
def get_nearby_complaints(
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius_km: float = Query(default=5.0, gt=0, le=100),
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> list[ComplaintSummary]:
    complaints = complaint_service.list_nearby_for_district(
        db, staff.district_id, latitude=latitude, longitude=longitude, radius_km=radius_km
    )
    return [complaint_service.to_complaint_summary(item) for item in complaints]


@router.get("/complaints/{complaint_id}", response_model=ComplaintRead)
def get_complaint(
    complaint_id: uuid.UUID,
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> ComplaintRead:
    complaint = complaint_service.get_complaint_for_officer(db, staff, complaint_id)
    return complaint_service.to_complaint_read(complaint)


@router.get("/complaints/{complaint_id}/timeline", response_model=list[ComplaintStatusHistoryRead])
def get_complaint_timeline(
    complaint_id: uuid.UUID,
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> list[ComplaintStatusHistoryRead]:
    complaint = complaint_service.get_complaint_for_officer(db, staff, complaint_id)
    history = complaint_status_history_repository.list_by_complaint(db, complaint.id)
    return complaint_service.to_timeline_read(history)


@router.get("/complaints/{complaint_id}/evidence", response_model=list[EvidenceRead])
def list_complaint_evidence(
    complaint_id: uuid.UUID,
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> list[EvidenceRead]:
    complaint = complaint_service.get_complaint_for_officer(db, staff, complaint_id)
    return evidence_service.list_evidence_with_urls(db, complaint.id)


@router.patch("/complaints/{complaint_id}/status", response_model=ComplaintRead)
def update_complaint_status(
    complaint_id: uuid.UUID,
    payload: ComplaintStatusUpdateRequest,
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> ComplaintRead:
    complaint = complaint_service.get_complaint_for_officer(db, staff, complaint_id)
    complaint = complaint_service.update_status(db, staff, complaint, payload.status, payload.reason)
    return complaint_service.to_complaint_read(complaint)


@router.post("/complaints/{complaint_id}/assign", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED)
def assign_inspector(
    complaint_id: uuid.UUID,
    payload: AssignmentCreateRequest,
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> AssignmentRead:
    complaint = complaint_service.get_complaint_for_officer(db, staff, complaint_id)
    assignment = assignment_service.assign_inspector(
        db,
        staff,
        complaint,
        inspector_staff_id=payload.inspector_staff_id,
        due_at=payload.due_at,
        notes=payload.notes,
    )
    return assignment_service.to_assignment_read(assignment)


@router.get("/complaints/{complaint_id}/assignment", response_model=AssignmentRead)
def get_complaint_assignment(
    complaint_id: uuid.UUID,
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> AssignmentRead:
    complaint = complaint_service.get_complaint_for_officer(db, staff, complaint_id)
    assignment = assignment_service.get_assignment_for_officer(db, staff, complaint)
    return assignment_service.to_assignment_read(assignment)


@router.get("/complaints/{complaint_id}/inspection", response_model=InspectionRead)
def get_complaint_inspection(
    complaint_id: uuid.UUID,
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> InspectionRead:
    complaint = complaint_service.get_complaint_for_officer(db, staff, complaint_id)
    inspection = inspection_service.get_inspection_for_officer(db, staff, complaint)
    return inspection_service.to_inspection_read(inspection)
