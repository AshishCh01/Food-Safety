import math

from app.utils.exceptions import InvalidCoordinatesError

MIN_LATITUDE, MAX_LATITUDE = -90.0, 90.0
MIN_LONGITUDE, MAX_LONGITUDE = -180.0, 180.0

EARTH_RADIUS_KM = 6371.0


def validate_latitude(value: float) -> None:
    if not (MIN_LATITUDE <= value <= MAX_LATITUDE):
        raise InvalidCoordinatesError(f"Latitude must be between {MIN_LATITUDE} and {MAX_LATITUDE}.")


def validate_longitude(value: float) -> None:
    if not (MIN_LONGITUDE <= value <= MAX_LONGITUDE):
        raise InvalidCoordinatesError(f"Longitude must be between {MIN_LONGITUDE} and {MAX_LONGITUDE}.")


def validate_coordinates(latitude: float | None, longitude: float | None) -> None:
    """Validates a lat/lng pair supplied together at a system boundary.

    Either both must be present or both absent - a lone coordinate is not
    a usable location and is rejected rather than silently ignored.
    """
    if (latitude is None) != (longitude is None):
        raise InvalidCoordinatesError("Latitude and longitude must be provided together.")
    if latitude is not None and longitude is not None:
        validate_latitude(latitude)
        validate_longitude(longitude)


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points, used for nearest-district
    resolution and as the non-PostGIS fallback for proximity queries."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def to_wkt_point(latitude: float, longitude: float) -> str:
    return f"SRID=4326;POINT({longitude} {latitude})"
