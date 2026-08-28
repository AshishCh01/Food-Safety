from app.services import analytics_service
from app.tests.factories import create_complaint, create_complaint_category, create_district, create_division, create_user
from app.utils.enums import ComplaintStatus


def _make_complaint(db_session, citizen, district, category, status):
    return create_complaint(db_session, citizen, district, category, status=status)


def test_status_bucket_boundaries_cover_every_lifecycle_status(db_session) -> None:
    """Every ComplaintStatus must land in exactly one KPI bucket (pending/
    active/resolved/rejected) so total_complaints always equals the sum of
    the four buckets - this pins that invariant for statuses that are easy
    to miscategorize (CLOSED, DUPLICATE, INSUFFICIENT_EVIDENCE, CANCELLED)."""
    division = create_division(db_session)
    district = create_district(db_session, division)
    category = create_complaint_category(db_session)
    citizen = create_user(db_session, email="citizen@example.com")

    for status in ComplaintStatus:
        _make_complaint(db_session, citizen, district, category, status)

    analytics = analytics_service.get_district_analytics(db_session, district.id, district.name)

    assert analytics.total_complaints == len(list(ComplaintStatus))
    bucket_sum = (
        analytics.pending_complaints
        + analytics.active_complaints
        + analytics.resolved_complaints
        + analytics.rejected_complaints
    )
    assert bucket_sum == analytics.total_complaints

    # CLOSED is a terminal, non-rejected outcome - it belongs with RESOLVED.
    assert ComplaintStatus.CLOSED in analytics_service.RESOLVED_STATUSES
    # These are all non-progress terminal statuses that are not an
    # affirmative resolution.
    for status in (ComplaintStatus.DUPLICATE, ComplaintStatus.INSUFFICIENT_EVIDENCE, ComplaintStatus.CANCELLED):
        assert status in analytics_service.REJECTED_STATUSES


def test_district_with_zero_complaints_returns_zeroed_analytics(db_session) -> None:
    division = create_division(db_session)
    district = create_district(db_session, division)

    analytics = analytics_service.get_district_analytics(db_session, district.id, district.name)

    assert analytics.total_complaints == 0
    assert analytics.average_resolution_hours is None
    assert analytics.inspector_workload == []
    assert analytics.inspection_outcomes.total_inspections == 0
    assert all(item.count == 0 for item in analytics.status_breakdown)
    assert len(analytics.status_breakdown) == len(list(ComplaintStatus))
