from sqlalchemy.orm import Session

from app.models.district import District
from app.repositories import district_repository
from app.schemas.district import DistrictRead
from app.utils.exceptions import DistrictNotResolvableError
from app.utils.geo import haversine_distance_km, validate_coordinates


def list_districts(db: Session, *, is_active: bool | None = None) -> list[District]:
    return district_repository.list_all(db, is_active=is_active)


def resolve_district_for_point(db: Session, latitude: float, longitude: float) -> District:
    """Derives the district a reported location falls in from the district
    nearest to it, rather than trusting a client-supplied district field as
    the routing source of truth (see docs/PROJECT_SPEC.md section 11).

    Uses nearest-centroid matching (see District.centroid_latitude/
    centroid_longitude) since the project does not yet have surveyed
    district boundary polygons for true point-in-polygon lookup.
    """
    validate_coordinates(latitude, longitude)
    districts = district_repository.list_all(db, is_active=True)
    candidates = [d for d in districts if d.centroid_latitude is not None and d.centroid_longitude is not None]
    if not candidates:
        raise DistrictNotResolvableError()

    return min(
        candidates,
        key=lambda d: haversine_distance_km(
            latitude, longitude, float(d.centroid_latitude), float(d.centroid_longitude)
        ),
    )


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
