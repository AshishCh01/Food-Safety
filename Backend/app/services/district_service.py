from sqlalchemy.orm import Session

from app.models.district import District
from app.repositories import district_repository
from app.schemas.district import DistrictRead
from app.utils.exceptions import DistrictNotResolvableError
from app.utils.geo import haversine_distance_km, validate_coordinates

# Maharashtra's own extent is roughly 800km end-to-end, so a point more than
# this far from the nearest district centroid isn't "the edge of some
# district's catchment", it's a coordinate typo, a client-side geolocation
# glitch, or a complaint genuinely filed from outside the state - none of
# which should be silently routed into whichever district happens to be
# nearest (docs/PROJECT_AUDIT_REPORT.md finding 1.10).
_MAX_RESOLUTION_DISTANCE_KM = 150.0


def list_districts(db: Session, *, is_active: bool | None = None) -> list[District]:
    return district_repository.list_all(db, is_active=is_active)


def resolve_district_for_point(db: Session, latitude: float, longitude: float) -> District:
    """Derives the district a reported location falls in from the district
    nearest to it, rather than trusting a client-supplied district field as
    the routing source of truth (see docs/PROJECT_SPEC.md section 11).

    Uses nearest-centroid matching (see District.centroid_latitude/
    centroid_longitude) since the project does not yet have surveyed
    district boundary polygons for true point-in-polygon lookup. Points
    further than `_MAX_RESOLUTION_DISTANCE_KM` from the nearest centroid are
    rejected as unresolvable rather than silently misfiled into it.
    """
    validate_coordinates(latitude, longitude)
    districts = district_repository.list_all(db, is_active=True)
    candidates = [d for d in districts if d.centroid_latitude is not None and d.centroid_longitude is not None]
    if not candidates:
        raise DistrictNotResolvableError()

    nearest = min(
        candidates,
        key=lambda d: haversine_distance_km(
            latitude, longitude, float(d.centroid_latitude), float(d.centroid_longitude)
        ),
    )
    nearest_distance_km = haversine_distance_km(
        latitude, longitude, float(nearest.centroid_latitude), float(nearest.centroid_longitude)
    )
    if nearest_distance_km > _MAX_RESOLUTION_DISTANCE_KM:
        raise DistrictNotResolvableError(
            "The supplied location is too far from any known district to resolve reliably."
        )

    return nearest


def to_district_read(district: District) -> DistrictRead:
    return DistrictRead(
        id=district.id,
        name=district.name,
        code=district.code,
        division_id=district.division_id,
        division_name=district.division.name,
        centroid_latitude=float(district.centroid_latitude) if district.centroid_latitude is not None else None,
        centroid_longitude=float(district.centroid_longitude) if district.centroid_longitude is not None else None,
        is_active=district.is_active,
    )
