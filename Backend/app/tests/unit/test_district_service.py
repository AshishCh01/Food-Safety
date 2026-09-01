import pytest
from sqlalchemy.orm import Session

from app.services import district_service
from app.tests.factories import create_district, create_division
from app.utils.exceptions import DistrictNotResolvableError, InvalidCoordinatesError


def _setup_pune_and_nagpur(db_session: Session):
    division = create_division(db_session, name="Test Division", code="TST")
    pune = create_district(
        db_session, division, name="Pune", code="PUN", centroid_latitude=18.5204, centroid_longitude=73.8567
    )
    nagpur = create_district(
        db_session, division, name="Nagpur", code="NGP", centroid_latitude=21.1458, centroid_longitude=79.0882
    )
    return pune, nagpur


def test_resolve_district_for_point_picks_nearest_centroid(db_session: Session):
    pune, nagpur = _setup_pune_and_nagpur(db_session)

    resolved = district_service.resolve_district_for_point(db_session, 18.53, 73.86)

    assert resolved.id == pune.id


def test_resolve_district_for_point_picks_the_other_nearest_centroid(db_session: Session):
    pune, nagpur = _setup_pune_and_nagpur(db_session)

    resolved = district_service.resolve_district_for_point(db_session, 21.10, 79.05)

    assert resolved.id == nagpur.id


def test_resolve_district_for_point_ignores_inactive_districts(db_session: Session):
    division = create_division(db_session, name="Test Division", code="TST")
    pune = create_district(
        db_session, division, name="Pune", code="PUN", centroid_latitude=18.5204, centroid_longitude=73.8567
    )
    # Deliberately close to Pune (~70km, well within the resolution distance
    # bound) rather than using the real Nagpur coordinates (~700km from
    # Pune) - the point below must land within range of the active fallback
    # (Pune) for this test to isolate "inactive districts are skipped" from
    # the distance-bound check covered separately below.
    nearby_inactive = create_district(
        db_session, division, name="Nearby Inactive", code="NIA", centroid_latitude=19.0, centroid_longitude=74.3
    )
    nearby_inactive.is_active = False
    db_session.commit()

    # A point right next to the inactive district should still resolve to
    # Pune since the inactive district is not a valid routing target.
    resolved = district_service.resolve_district_for_point(db_session, 19.01, 74.31)

    assert resolved.id == pune.id


def test_resolve_district_for_point_rejects_invalid_coordinates(db_session: Session):
    _setup_pune_and_nagpur(db_session)

    with pytest.raises(InvalidCoordinatesError):
        district_service.resolve_district_for_point(db_session, 999.0, 73.8567)


def test_resolve_district_for_point_with_no_centroid_data_raises(db_session: Session):
    division = create_division(db_session, name="Test Division", code="TST")
    create_district(db_session, division, name="Pune", code="PUN", centroid_latitude=None, centroid_longitude=None)

    with pytest.raises(DistrictNotResolvableError):
        district_service.resolve_district_for_point(db_session, 18.53, 73.86)


def test_resolve_district_for_point_rejects_point_far_outside_any_district(db_session: Session):
    _setup_pune_and_nagpur(db_session)

    # Roughly London - thousands of km from both district centroids, well
    # past the sanity bound, even though both coordinates are individually
    # in-range and would otherwise silently resolve to whichever centroid is
    # least-far-away.
    with pytest.raises(DistrictNotResolvableError):
        district_service.resolve_district_for_point(db_session, 51.5074, -0.1278)


def test_resolve_district_for_point_accepts_point_within_max_distance(db_session: Session):
    pune, _nagpur = _setup_pune_and_nagpur(db_session)

    # ~0.3 degrees off Pune's centroid is well within the sanity bound and
    # should still resolve normally.
    resolved = district_service.resolve_district_for_point(db_session, 18.8, 74.1)

    assert resolved.id == pune.id
