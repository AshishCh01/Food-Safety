import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.complaint import Complaint
from app.utils.enums import ComplaintPriority, ComplaintStatus
from app.utils.geo import haversine_distance_km

_EAGER_OPTIONS = (
    joinedload(Complaint.business),
    joinedload(Complaint.district),
    joinedload(Complaint.category),
    joinedload(Complaint.submitted_by),
)


def get_by_id(db: Session, complaint_id: uuid.UUID) -> Complaint | None:
    stmt = select(Complaint).where(Complaint.id == complaint_id).options(*_EAGER_OPTIONS)
    return db.execute(stmt).scalar_one_or_none()


def get_by_complaint_number(db: Session, complaint_number: str) -> Complaint | None:
    stmt = select(Complaint).where(Complaint.complaint_number == complaint_number).options(*_EAGER_OPTIONS)
    return db.execute(stmt).scalar_one_or_none()


def create(db: Session, complaint: Complaint) -> Complaint:
    db.add(complaint)
    db.flush()
    return complaint


def list_by_citizen(
    db: Session,
    user_id: uuid.UUID,
    *,
    status: ComplaintStatus | None = None,
    category_id: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Complaint], int]:
    stmt = select(Complaint).where(Complaint.submitted_by_user_id == user_id)
    if status is not None:
        stmt = stmt.where(Complaint.status == status)
    if category_id is not None:
        stmt = stmt.where(Complaint.category_id == category_id)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    stmt = (
        stmt.options(*_EAGER_OPTIONS)
        .order_by(Complaint.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(db.execute(stmt).scalars().all())
    return items, total


MAP_MARKER_LIMIT = 1000

_MAP_EAGER_OPTIONS = (joinedload(Complaint.business), joinedload(Complaint.category))


def list_map_markers_by_district(
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
    """Lists complaints with coordinates for map display, filtered by a
    Leaflet-style bounding box plus the usual status/priority/category/date
    filters. Uses the plain latitude/longitude columns (not the PostGIS
    `location` column) since a bounding box is a simple range comparison
    that works identically across PostgreSQL and the SQLite test database -
    see app/core/geo_types.py for why that dialect split exists.
    """
    stmt = select(Complaint).where(
        Complaint.district_id == district_id,
        Complaint.latitude.is_not(None),
        Complaint.longitude.is_not(None),
    )
    if min_lat is not None:
        stmt = stmt.where(Complaint.latitude >= min_lat)
    if max_lat is not None:
        stmt = stmt.where(Complaint.latitude <= max_lat)
    if min_lng is not None:
        stmt = stmt.where(Complaint.longitude >= min_lng)
    if max_lng is not None:
        stmt = stmt.where(Complaint.longitude <= max_lng)
    if status is not None:
        stmt = stmt.where(Complaint.status == status)
    if priority is not None:
        stmt = stmt.where(Complaint.priority == priority)
    if category_id is not None:
        stmt = stmt.where(Complaint.category_id == category_id)
    if date_from is not None:
        stmt = stmt.where(Complaint.created_at >= date_from)
    if date_to is not None:
        stmt = stmt.where(Complaint.created_at <= date_to)

    stmt = stmt.options(*_MAP_EAGER_OPTIONS).order_by(Complaint.created_at.desc()).limit(MAP_MARKER_LIMIT)
    return list(db.execute(stmt).scalars().all())


def list_within_radius(
    db: Session,
    district_id: uuid.UUID,
    *,
    latitude: float,
    longitude: float,
    radius_km: float,
    limit: int = 200,
) -> list[Complaint]:
    """Proximity search around a point, scoped to a district.

    Uses real PostGIS (ST_DWithin/ST_Distance on the geography column) on
    PostgreSQL. The project's test suite runs against in-memory SQLite
    (app/tests/conftest.py), which has no spatial extension, so this falls
    back to an equivalent Python-side Haversine filter there - the same
    dialect-conditional approach already used for StaffProfile's partial
    index (app/models/staff_profile.py).
    """
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        point = func.ST_GeogFromText(f"SRID=4326;POINT({longitude} {latitude})")
        distance_expr = func.ST_Distance(Complaint.location, point)
        stmt = (
            select(Complaint)
            .where(
                Complaint.district_id == district_id,
                Complaint.location.is_not(None),
                func.ST_DWithin(Complaint.location, point, radius_km * 1000),
            )
            .options(*_EAGER_OPTIONS)
            .order_by(distance_expr)
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())

    stmt = select(Complaint).where(
        Complaint.district_id == district_id,
        Complaint.latitude.is_not(None),
        Complaint.longitude.is_not(None),
    )
    candidates = list(db.execute(stmt.options(*_EAGER_OPTIONS)).scalars().all())
    within_radius = [
        c
        for c in candidates
        if haversine_distance_km(latitude, longitude, float(c.latitude), float(c.longitude)) <= radius_km
    ]
    within_radius.sort(key=lambda c: haversine_distance_km(latitude, longitude, float(c.latitude), float(c.longitude)))
    return within_radius[:limit]


def list_by_business(
    db: Session,
    business_id: uuid.UUID,
    district_id: uuid.UUID,
    *,
    exclude_complaint_id: uuid.UUID | None = None,
    limit: int = 5,
) -> list[Complaint]:
    """Other complaints against the same business, scoped to `district_id` (the
    caller's own district) so this can never surface another district's data -
    used by the Inspector Assistant's get_previous_complaints tool."""
    stmt = select(Complaint).where(Complaint.business_id == business_id, Complaint.district_id == district_id)
    if exclude_complaint_id is not None:
        stmt = stmt.where(Complaint.id != exclude_complaint_id)
    stmt = stmt.options(*_EAGER_OPTIONS).order_by(Complaint.created_at.desc()).limit(limit)
    return list(db.execute(stmt).scalars().all())


def list_by_district(
    db: Session,
    district_id: uuid.UUID,
    *,
    status: ComplaintStatus | None = None,
    priority: ComplaintPriority | None = None,
    category_id: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Complaint], int]:
    stmt = select(Complaint).where(Complaint.district_id == district_id)
    if status is not None:
        stmt = stmt.where(Complaint.status == status)
    if priority is not None:
        stmt = stmt.where(Complaint.priority == priority)
    if category_id is not None:
        stmt = stmt.where(Complaint.category_id == category_id)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    stmt = (
        stmt.options(*_EAGER_OPTIONS)
        .order_by(Complaint.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(db.execute(stmt).scalars().all())
    return items, total
