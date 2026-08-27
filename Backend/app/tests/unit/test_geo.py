import pytest

from app.utils.exceptions import InvalidCoordinatesError
from app.utils.geo import haversine_distance_km, to_wkt_point, validate_coordinates, validate_latitude, validate_longitude


def test_validate_latitude_accepts_boundary_values():
    validate_latitude(90.0)
    validate_latitude(-90.0)
    validate_latitude(0.0)


@pytest.mark.parametrize("value", [90.0001, -90.0001, 180, -400])
def test_validate_latitude_rejects_out_of_range(value):
    with pytest.raises(InvalidCoordinatesError):
        validate_latitude(value)


def test_validate_longitude_accepts_boundary_values():
    validate_longitude(180.0)
    validate_longitude(-180.0)


@pytest.mark.parametrize("value", [180.0001, -180.0001, 400])
def test_validate_longitude_rejects_out_of_range(value):
    with pytest.raises(InvalidCoordinatesError):
        validate_longitude(value)


def test_validate_coordinates_allows_both_absent():
    validate_coordinates(None, None)


def test_validate_coordinates_rejects_partial_pair():
    with pytest.raises(InvalidCoordinatesError):
        validate_coordinates(18.5, None)
    with pytest.raises(InvalidCoordinatesError):
        validate_coordinates(None, 73.8)


def test_validate_coordinates_rejects_invalid_pair():
    with pytest.raises(InvalidCoordinatesError):
        validate_coordinates(999.0, 73.8)


def test_haversine_distance_same_point_is_zero():
    assert haversine_distance_km(18.5204, 73.8567, 18.5204, 73.8567) == pytest.approx(0.0, abs=1e-6)


def test_haversine_distance_pune_to_nagpur_is_roughly_correct():
    # Pune -> Nagpur is approximately 620km as the crow flies.
    distance = haversine_distance_km(18.5204, 73.8567, 21.1458, 79.0882)
    assert 580 < distance < 660


def test_to_wkt_point_format():
    assert to_wkt_point(18.5204, 73.8567) == "SRID=4326;POINT(73.8567 18.5204)"
