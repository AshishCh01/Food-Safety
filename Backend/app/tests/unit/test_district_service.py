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
    nagpur = create_district(
        db_session, division, name="Nagpur", code="NGP", centroid_latitude=21.1458, centroid_longitude=79.0882
    )
    nagpur.is_active = False
    db_session.commit()

    # A point right next to Nagpur should still resolve to Pune since Nagpur
    # is inactive and therefore not a valid routing target.
    resolved = district_service.resolve_district_for_point(db_session, 21.10, 79.05)

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
