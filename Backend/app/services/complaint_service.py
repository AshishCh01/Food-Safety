import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.complaint import Complaint
from app.models.complaint_status_history import ComplaintStatusHistory
from app.models.district import District
from app.models.staff_profile import StaffProfile
from app.models.user import User
from app.repositories import (
    audit_log_repository,
    complaint_category_repository,
    complaint_repository,
    complaint_sequence_repository,
    complaint_status_history_repository,
    district_repository,
)
from app.schemas.business import BusinessRead
from app.schemas.complaint import (
    ComplaintCreateRequest,
    ComplaintMapMarker,
    ComplaintRead,
    ComplaintSummary,
)
from app.schemas.complaint_status_history import ComplaintStatusHistoryRead
from app.services import business_service, district_service
from app.utils.enums import ComplaintPriority, ComplaintStatus
from app.utils.exceptions import (
    CategoryNotFoundError,
    ComplaintNotFoundError,
    InvalidComplaintStatusTransitionError,
    NotFoundError,
)
from app.utils.geo import validate_coordinates

# Transitions this phase supports. Assignment/inspection/resolution states
# are Phase 4+ territory and are intentionally not reachable here.
ALLOWED_TRANSITIONS: dict[ComplaintStatus, set[ComplaintStatus]] = {
    ComplaintStatus.SUBMITTED: {
        ComplaintStatus.UNDER_REVIEW,
        ComplaintStatus.REJECTED,
        ComplaintStatus.DUPLICATE,
        ComplaintStatus.INSUFFICIENT_EVIDENCE,
    },
    ComplaintStatus.UNDER_REVIEW: {
        ComplaintStatus.NEEDS_INFORMATION,
        ComplaintStatus.VERIFIED,
        ComplaintStatus.REJECTED,
        ComplaintStatus.DUPLICATE,
        ComplaintStatus.INSUFFICIENT_EVIDENCE,
    },
    ComplaintStatus.NEEDS_INFORMATION: {
        ComplaintStatus.UNDER_REVIEW,
        ComplaintStatus.REJECTED,
    },
    # These three are officer-freeform decisions made after reviewing
    # inspection results; the earlier VERIFIED->...->INSPECTION_COMPLETED
    # chain is system-driven (see apply_system_transition) and intentionally
    # not reachable through the generic status-update endpoint.
    ComplaintStatus.INSPECTION_COMPLETED: {
        ComplaintStatus.ACTION_IN_PROGRESS,
        ComplaintStatus.RESOLVED,
        ComplaintStatus.CLOSED,
    },
    ComplaintStatus.ACTION_IN_PROGRESS: {
        ComplaintStatus.RESOLVED,
        ComplaintStatus.CLOSED,
    },
    ComplaintStatus.RESOLVED: {
        ComplaintStatus.CLOSED,
    },
}


def _resolve_district(db: Session, payload: ComplaintCreateRequest) -> District:
    """District routing follows docs/PROJECT_SPEC.md section 11: a reported
    location is the authoritative source of district routing, not a
    client-supplied district field. When coordinates are present, the
    backend derives the district from them (overriding a mismatched
    client-selected value); the client's district_id is only trusted when
    no location was captured (e.g. GPS unavailable).
    """
    if payload.latitude is not None and payload.longitude is not None:
        return district_service.resolve_district_for_point(db, payload.latitude, payload.longitude)

    district = district_repository.get_by_id(db, payload.district_id)
    if district is None or not district.is_active:
        raise NotFoundError("District was not found.")
    return district


def create_complaint(db: Session, citizen: User, payload: ComplaintCreateRequest) -> Complaint:
    validate_coordinates(payload.latitude, payload.longitude)

    category = complaint_category_repository.get_by_id(db, payload.category_id)
    if category is None or not category.is_active:
        raise CategoryNotFoundError()

    district = _resolve_district(db, payload)

    business = business_service.get_or_create_business(
        db, district_id=district.id, created_by_user_id=citizen.id, payload=payload.business
    )

    reported_at = payload.reported_at or datetime.now(timezone.utc)
    year = reported_at.year
    seq = complaint_sequence_repository.next_sequence_number(db, district.id, year)
    complaint_number = f"MH-{district.code}-{year}-{seq:06d}"

    complaint = Complaint(
        complaint_number=complaint_number,
        submitted_by_user_id=citizen.id,
        business_id=business.id,
        district_id=district.id,
        category_id=category.id,
        title=payload.title,
        description=payload.description,
        status=ComplaintStatus.SUBMITTED,
        priority=payload.priority,
        latitude=payload.latitude,
        longitude=payload.longitude,
        address_line=payload.address_line,
        reported_at=reported_at,
    )
    complaint_repository.create(db, complaint)

    complaint_status_history_repository.create(
        db,
        complaint_id=complaint.id,
        old_status=None,
        new_status=ComplaintStatus.SUBMITTED,
        changed_by_user_id=citizen.id,
    )

    db.commit()
    return complaint_repository.get_by_id(db, complaint.id)


def get_complaint_for_citizen(db: Session, citizen_id: uuid.UUID, complaint_id: uuid.UUID) -> Complaint:
    complaint = complaint_repository.get_by_id(db, complaint_id)
    if complaint is None or complaint.submitted_by_user_id != citizen_id:
        raise ComplaintNotFoundError()
    return complaint


def get_complaint_for_officer(db: Session, staff: StaffProfile, complaint_id: uuid.UUID) -> Complaint:
    complaint = complaint_repository.get_by_id(db, complaint_id)
    if complaint is None or complaint.district_id != staff.district_id:
        raise ComplaintNotFoundError()
    return complaint


def list_for_citizen(
    db: Session,
    citizen_id: uuid.UUID,
    *,
    status: ComplaintStatus | None,
    category_id: uuid.UUID | None,
    page: int,
    page_size: int,
) -> tuple[list[Complaint], int]:
    return complaint_repository.list_by_citizen(
        db, citizen_id, status=status, category_id=category_id, page=page, page_size=page_size
    )


def list_for_district(
    db: Session,
    district_id: uuid.UUID,
    *,
    status: ComplaintStatus | None,
    priority: ComplaintPriority | None,
    category_id: uuid.UUID | None,
    page: int,
    page_size: int,
) -> tuple[list[Complaint], int]:
    return complaint_repository.list_by_district(
        db, district_id, status=status, priority=priority, category_id=category_id, page=page, page_size=page_size
    )


def list_map_markers_for_district(
    db: Session,
    district_id: uuid.UUID,
    *,
    min_lat: float | None = None,
    min_lng: float | None = None,
    max_lat: float | None = None,
    max_lng: float | None = None,
    status: ComplaintStatus | None = None,
    priority: ComplaintPriority | None = None,
    category_id: uuid.UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[Complaint]:
    return complaint_repository.list_map_markers_by_district(
        db,
        district_id,
        min_lat=min_lat,
        min_lng=min_lng,
        max_lat=max_lat,
        max_lng=max_lng,
        status=status,
        priority=priority,
        category_id=category_id,
        date_from=date_from,
        date_to=date_to,
    )


def list_nearby_for_district(
    db: Session,
    district_id: uuid.UUID,
    *,
    latitude: float,
    longitude: float,
    radius_km: float,
) -> list[Complaint]:
    validate_coordinates(latitude, longitude)
    return complaint_repository.list_within_radius(
        db, district_id, latitude=latitude, longitude=longitude, radius_km=radius_km
    )


def _apply_transition(
    db: Session,
    complaint: Complaint,
    new_status: ComplaintStatus,
    changed_by_user_id: uuid.UUID,
    reason: str | None = None,
) -> Complaint:
    old_status = complaint.status
    complaint.status = new_status
    if new_status == ComplaintStatus.VERIFIED:
        complaint.verified_at = datetime.now(timezone.utc)
    if new_status == ComplaintStatus.RESOLVED:
        complaint.resolved_at = datetime.now(timezone.utc)
    db.flush()

    complaint_status_history_repository.create(
        db,
        complaint_id=complaint.id,
        old_status=old_status,
        new_status=new_status,
        changed_by_user_id=changed_by_user_id,
        reason=reason,
    )
    audit_log_repository.record(
        db,
        actor_user_id=changed_by_user_id,
        action="complaint_status_changed",
        entity_type="complaint",
        entity_id=complaint.id,
        details={"old_status": old_status.value if old_status else None, "new_status": new_status.value},
    )

    db.commit()
    return complaint_repository.get_by_id(db, complaint.id)


def update_status(
    db: Session,
    staff: StaffProfile,
    complaint: Complaint,
    new_status: ComplaintStatus,
    reason: str | None,
) -> Complaint:
    allowed = ALLOWED_TRANSITIONS.get(complaint.status, set())
    if new_status not in allowed:
        raise InvalidComplaintStatusTransitionError(
            f"Cannot transition a complaint from '{complaint.status.value}' to '{new_status.value}'."
        )
    return _apply_transition(db, complaint, new_status, staff.user_id, reason)


def apply_system_transition(
    db: Session,
    complaint: Complaint,
    new_status: ComplaintStatus,
    changed_by_user_id: uuid.UUID,
    reason: str | None = None,
) -> Complaint:
    """Applies a status transition driven by a domain action (assignment,
    inspection lifecycle) rather than the officer's freeform status dropdown.

    Callers are responsible for validating their own domain-specific
    precondition before calling this - it does not check ALLOWED_TRANSITIONS.
    """
    return _apply_transition(db, complaint, new_status, changed_by_user_id, reason)


def to_complaint_read(complaint: Complaint) -> ComplaintRead:
    business_read: BusinessRead | None = (
        business_service.to_business_read(complaint.business) if complaint.business is not None else None
    )
    return ComplaintRead(
        id=complaint.id,
        complaint_number=complaint.complaint_number,
        title=complaint.title,
        description=complaint.description,
        status=complaint.status,
        priority=complaint.priority,
        category_id=complaint.category_id,
        category_name=complaint.category.name,
        district_id=complaint.district_id,
        district_name=complaint.district.name,
        business=business_read,
        latitude=float(complaint.latitude) if complaint.latitude is not None else None,
        longitude=float(complaint.longitude) if complaint.longitude is not None else None,
        address_line=complaint.address_line,
        reported_at=complaint.reported_at,
        verified_at=complaint.verified_at,
        resolved_at=complaint.resolved_at,
        submitted_by_user_id=complaint.submitted_by_user_id,
        submitted_by_name=complaint.submitted_by.full_name,
        created_at=complaint.created_at,
        updated_at=complaint.updated_at,
    )


def to_complaint_summary(complaint: Complaint) -> ComplaintSummary:
    return ComplaintSummary(
        id=complaint.id,
        complaint_number=complaint.complaint_number,
        title=complaint.title,
        category_name=complaint.category.name,
        status=complaint.status,
        priority=complaint.priority,
        district_name=complaint.district.name,
        created_at=complaint.created_at,
    )


def to_map_marker(complaint: Complaint) -> ComplaintMapMarker:
    return ComplaintMapMarker(
        id=complaint.id,
        complaint_number=complaint.complaint_number,
        title=complaint.title,
        status=complaint.status,
        priority=complaint.priority,
        category_id=complaint.category_id,
        category_name=complaint.category.name,
        latitude=float(complaint.latitude),
        longitude=float(complaint.longitude),
        business_name=complaint.business.business_name if complaint.business else None,
        created_at=complaint.created_at,
    )


def to_timeline_read(history: list[ComplaintStatusHistory]) -> list[ComplaintStatusHistoryRead]:
    return [
        ComplaintStatusHistoryRead(
            id=entry.id,
            old_status=entry.old_status,
            new_status=entry.new_status,
            changed_by_user_id=entry.changed_by_user_id,
            changed_by_name=entry.changed_by.full_name,
            reason=entry.reason,
            created_at=entry.created_at,
        )
        for entry in history
    ]
