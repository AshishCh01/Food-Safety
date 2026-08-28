import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import Select, case, func, select
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.complaint import Complaint
from app.models.complaint_category import ComplaintCategory
from app.models.district import District
from app.models.division import Division
from app.models.inspection import Inspection
from app.models.inspection_finding import InspectionFinding
from app.models.staff_profile import StaffProfile
from app.models.user import User
from app.utils.enums import AssignmentStatus, ComplaintPriority, ComplaintStatus, InspectionStatus, UserRole


def _scoped(stmt: Select, district_id: uuid.UUID | None) -> Select:
    if district_id is not None:
        return stmt.where(Complaint.district_id == district_id)
    return stmt


def status_breakdown(db: Session, district_id: uuid.UUID | None = None) -> dict[ComplaintStatus, int]:
    stmt = _scoped(select(Complaint.status, func.count()).group_by(Complaint.status), district_id)
    return dict(db.execute(stmt).all())


def priority_breakdown(db: Session, district_id: uuid.UUID | None = None) -> dict[ComplaintPriority, int]:
    stmt = _scoped(select(Complaint.priority, func.count()).group_by(Complaint.priority), district_id)
    return dict(db.execute(stmt).all())


def category_breakdown(db: Session, district_id: uuid.UUID | None = None) -> list[tuple[uuid.UUID, str, int]]:
    stmt = (
        select(ComplaintCategory.id, ComplaintCategory.name, func.count(Complaint.id))
        .join(Complaint, Complaint.category_id == ComplaintCategory.id)
        .group_by(ComplaintCategory.id, ComplaintCategory.name)
        .order_by(ComplaintCategory.name)
    )
    stmt = _scoped(stmt, district_id)
    return list(db.execute(stmt).all())


def complaint_trend(
    db: Session, district_id: uuid.UUID | None = None, *, days: int = 30
) -> list[tuple[str, int]]:
    """Daily complaint counts for the trailing `days` days. Uses `date()`
    rather than `CAST(... AS DATE)` since PostgreSQL and the SQLite test
    database both implement `date()` on a timestamp identically, whereas a
    DATE cast on SQLite leaves the original datetime string untouched (no
    DATE type affinity) and would silently break the day grouping there."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    day_expr = func.date(Complaint.created_at).label("day")
    stmt = (
        select(day_expr, func.count())
        .where(Complaint.created_at >= since)
        .group_by(day_expr)
        .order_by(day_expr)
    )
    stmt = _scoped(stmt, district_id)
    return list(db.execute(stmt).all())


def average_resolution_hours(db: Session, district_id: uuid.UUID | None = None) -> float | None:
    """Computed in Python rather than via SQL EXTRACT(EPOCH...), which has no
    SQLite equivalent - the same cross-dialect tradeoff as
    haversine_distance_km in complaint_repository.list_within_radius. Fine at
    this data scale since it only fetches two timestamp columns per resolved
    complaint."""
    stmt = select(Complaint.reported_at, Complaint.resolved_at).where(Complaint.resolved_at.is_not(None))
    stmt = _scoped(stmt, district_id)
    rows = db.execute(stmt).all()
    if not rows:
        return None
    total_seconds = sum((resolved_at - reported_at).total_seconds() for reported_at, resolved_at in rows)
    return round((total_seconds / len(rows)) / 3600, 2)


def inspector_workload(db: Session, district_id: uuid.UUID) -> list[tuple]:
    stmt = (
        select(
            StaffProfile.id,
            User.full_name,
            func.count(Assignment.id),
            func.sum(case((Assignment.status == AssignmentStatus.ASSIGNED, 1), else_=0)),
            func.sum(case((Assignment.status == AssignmentStatus.IN_PROGRESS, 1), else_=0)),
            func.sum(case((Assignment.status == AssignmentStatus.COMPLETED, 1), else_=0)),
        )
        .select_from(StaffProfile)
        .join(User, User.id == StaffProfile.user_id)
        .outerjoin(Assignment, Assignment.assigned_to_staff_id == StaffProfile.id)
        .where(StaffProfile.district_id == district_id, StaffProfile.role == UserRole.INSPECTOR)
        .group_by(StaffProfile.id, User.full_name)
        .order_by(User.full_name)
    )
    return list(db.execute(stmt).all())


def inspection_status_breakdown(db: Session, district_id: uuid.UUID | None = None) -> dict[InspectionStatus, int]:
    stmt = select(Inspection.inspection_status, func.count())
    if district_id is not None:
        stmt = stmt.join(Complaint, Inspection.complaint_id == Complaint.id).where(
            Complaint.district_id == district_id
        )
    stmt = stmt.group_by(Inspection.inspection_status)
    return dict(db.execute(stmt).all())


def finding_compliance_breakdown(db: Session, district_id: uuid.UUID | None = None) -> dict[bool, int]:
    stmt = select(InspectionFinding.compliant, func.count())
    if district_id is not None:
        stmt = (
            stmt.join(Inspection, InspectionFinding.inspection_id == Inspection.id)
            .join(Complaint, Inspection.complaint_id == Complaint.id)
            .where(Complaint.district_id == district_id)
        )
    stmt = stmt.group_by(InspectionFinding.compliant)
    return dict(db.execute(stmt).all())


def district_status_counts(db: Session) -> list[tuple]:
    """One row per (active district, complaint status actually present),
    plus one row per district with a NULL status if it has zero complaints -
    used to build the statewide per-district breakdown in a single query
    rather than N+1 per-district lookups."""
    stmt = (
        select(District.id, District.name, Division.name, Complaint.status, func.count(Complaint.id))
        .select_from(District)
        .join(Division, District.division_id == Division.id)
        .outerjoin(Complaint, Complaint.district_id == District.id)
        .where(District.is_active.is_(True))
        .group_by(District.id, District.name, Division.name, Complaint.status)
        .order_by(District.name)
    )
    return list(db.execute(stmt).all())
