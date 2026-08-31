import uuid

from sqlalchemy.orm import Session

from app.repositories import analytics_repository
from app.schemas.analytics import (
    CategoryCount,
    DistrictAnalytics,
    DistrictSummary,
    InspectionOutcomes,
    InspectorWorkload,
    PriorityCount,
    StatewideAnalytics,
    StatusCount,
    TrendPoint,
)
from app.utils.enums import ComplaintPriority, ComplaintStatus, InspectionStatus

DEFAULT_TREND_DAYS = 30

# Status groupings for KPI buckets, derived from the complaint lifecycle in
# docs/PROJECT_SPEC.md section 9 / docs/DATABASE_SCHEMA.md section 12.
PENDING_STATUSES = (ComplaintStatus.SUBMITTED, ComplaintStatus.UNDER_REVIEW, ComplaintStatus.NEEDS_INFORMATION)
ACTIVE_STATUSES = (
    ComplaintStatus.VERIFIED,
    ComplaintStatus.ASSIGNED,
    ComplaintStatus.INSPECTION_SCHEDULED,
    ComplaintStatus.UNDER_INSPECTION,
    ComplaintStatus.INSPECTION_COMPLETED,
    ComplaintStatus.ACTION_IN_PROGRESS,
)
RESOLVED_STATUSES = (ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED)
REJECTED_STATUSES = (
    ComplaintStatus.REJECTED,
    ComplaintStatus.DUPLICATE,
    ComplaintStatus.INSUFFICIENT_EVIDENCE,
    ComplaintStatus.CANCELLED,
)


def _bucket_count(status_counts: dict[ComplaintStatus, int], statuses: tuple[ComplaintStatus, ...]) -> int:
    return sum(status_counts.get(status, 0) for status in statuses)


def _status_breakdown_list(status_counts: dict[ComplaintStatus, int]) -> list[StatusCount]:
    return [StatusCount(status=status, count=status_counts.get(status, 0)) for status in ComplaintStatus]


def _priority_breakdown_list(priority_counts: dict[ComplaintPriority, int]) -> list[PriorityCount]:
    return [
        PriorityCount(priority=priority, count=priority_counts.get(priority, 0)) for priority in ComplaintPriority
    ]


def _category_breakdown_list(rows) -> list[CategoryCount]:
    return [CategoryCount(category_id=category_id, category_name=name, count=count) for category_id, name, count in rows]


def _trend_list(rows) -> list[TrendPoint]:
    return [TrendPoint(date=day, count=count) for day, count in rows]


def _inspection_outcomes(
    inspection_status_counts: dict[InspectionStatus, int], finding_counts: dict[bool, int]
) -> InspectionOutcomes:
    return InspectionOutcomes(
        total_inspections=sum(inspection_status_counts.values()),
        scheduled=inspection_status_counts.get(InspectionStatus.SCHEDULED, 0),
        in_progress=inspection_status_counts.get(InspectionStatus.IN_PROGRESS, 0),
        completed=inspection_status_counts.get(InspectionStatus.COMPLETED, 0),
        compliant_findings=finding_counts.get(True, 0),
        non_compliant_findings=finding_counts.get(False, 0),
    )


def get_district_analytics(
    db: Session, district_id: uuid.UUID, district_name: str, *, trend_days: int = DEFAULT_TREND_DAYS
) -> DistrictAnalytics:
    """District-scoped operational KPIs (docs/PROJECT_SPEC.md section 19).
    `district_id`/`district_name` must come from the caller's own
    authenticated staff profile - this function does not itself verify
    district ownership, matching the existing pattern where scope is
    resolved once at the API boundary (get_current_staff_profile)."""
    status_counts = analytics_repository.status_breakdown(db, district_id)
    priority_counts = analytics_repository.priority_breakdown(db, district_id)
    category_rows = analytics_repository.category_breakdown(db, district_id)
    trend_rows = analytics_repository.complaint_trend(db, district_id, days=trend_days)
    avg_resolution = analytics_repository.average_resolution_hours(db, district_id)
    workload_rows = analytics_repository.inspector_workload(db, district_id)
    inspection_status_counts = analytics_repository.inspection_status_breakdown(db, district_id)
    finding_counts = analytics_repository.finding_compliance_breakdown(db, district_id)

    total = sum(status_counts.values())

    return DistrictAnalytics(
        district_id=district_id,
        district_name=district_name,
        total_complaints=total,
        pending_complaints=_bucket_count(status_counts, PENDING_STATUSES),
        active_complaints=_bucket_count(status_counts, ACTIVE_STATUSES),
        resolved_complaints=_bucket_count(status_counts, RESOLVED_STATUSES),
        rejected_complaints=_bucket_count(status_counts, REJECTED_STATUSES),
        status_breakdown=_status_breakdown_list(status_counts),
        category_breakdown=_category_breakdown_list(category_rows),
        priority_breakdown=_priority_breakdown_list(priority_counts),
        complaint_trend=_trend_list(trend_rows),
        average_resolution_hours=avg_resolution,
        inspector_workload=[
            InspectorWorkload(
                inspector_staff_id=staff_id,
                inspector_name=name,
                assigned_count=assigned or 0,
                in_progress_count=in_progress or 0,
                completed_count=completed or 0,
                total_count=total_count or 0,
            )
            for staff_id, name, total_count, assigned, in_progress, completed in workload_rows
        ],
        inspection_outcomes=_inspection_outcomes(inspection_status_counts, finding_counts),
    )


def get_statewide_analytics(db: Session, *, trend_days: int = DEFAULT_TREND_DAYS) -> StatewideAnalytics:
    """Statewide KPIs with a per-district breakdown, for the admin dashboard
    (docs/PROJECT_SPEC.md section 21). Admins have statewide access by role,
    so no district scope is applied here."""
    status_counts = analytics_repository.status_breakdown(db)
    priority_counts = analytics_repository.priority_breakdown(db)
    category_rows = analytics_repository.category_breakdown(db)
    trend_rows = analytics_repository.complaint_trend(db, days=trend_days)
    avg_resolution = analytics_repository.average_resolution_hours(db)
    district_rows = analytics_repository.district_status_counts(db)

    total = sum(status_counts.values())

    per_district: dict[uuid.UUID, dict] = {}
    for district_id, district_name, division_name, status, count in district_rows:
        entry = per_district.setdefault(
            district_id,
            {
                "district_id": district_id,
                "district_name": district_name,
                "division_name": division_name,
                "total_complaints": 0,
                "pending_complaints": 0,
                "active_complaints": 0,
                "resolved_complaints": 0,
                "rejected_complaints": 0,
            },
        )
        if status is None:
            continue
        entry["total_complaints"] += count
        if status in PENDING_STATUSES:
            entry["pending_complaints"] += count
        elif status in ACTIVE_STATUSES:
            entry["active_complaints"] += count
        elif status in RESOLVED_STATUSES:
            entry["resolved_complaints"] += count
        elif status in REJECTED_STATUSES:
            entry["rejected_complaints"] += count

    district_breakdown = [DistrictSummary(**entry) for entry in per_district.values()]

    return StatewideAnalytics(
        total_districts=len(district_breakdown),
        total_complaints=total,
        pending_complaints=_bucket_count(status_counts, PENDING_STATUSES),
        active_complaints=_bucket_count(status_counts, ACTIVE_STATUSES),
        resolved_complaints=_bucket_count(status_counts, RESOLVED_STATUSES),
        rejected_complaints=_bucket_count(status_counts, REJECTED_STATUSES),
        status_breakdown=_status_breakdown_list(status_counts),
        category_breakdown=_category_breakdown_list(category_rows),
        priority_breakdown=_priority_breakdown_list(priority_counts),
        complaint_trend=_trend_list(trend_rows),
        average_resolution_hours=avg_resolution,
        district_breakdown=district_breakdown,
    )
