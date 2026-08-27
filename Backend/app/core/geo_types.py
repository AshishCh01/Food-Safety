from geoalchemy2 import Geography
from sqlalchemy.types import Text, TypeDecorator

from app.utils.geo import to_wkt_point


class GeographyPoint(TypeDecorator):
    """A geography(Point, 4326) column on PostgreSQL/PostGIS.

    The project's test suite runs against an in-memory SQLite database
    (see app/tests/conftest.py) which has no spatial extension, so this
    degrades to a plain WKT text column there. Any code that needs real
    spatial operators (ST_DWithin, ST_Distance, ...) must branch on
    db.bind.dialect.name and fall back to Python-side calculations - see
    app/repositories/complaint_repository.py:list_within_radius for the
    established pattern.
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Geography(geometry_type="POINT", srid=4326))
        return dialect.type_descriptor(Text())


def sync_location_from_lat_lon(_mapper, _connection, target) -> None:
    """SQLAlchemy before_insert/before_update listener that keeps a model's
    `location` GeographyPoint column in sync with its `latitude`/`longitude`
    columns, so callers only ever need to set lat/lon (matching the existing
    Business/Complaint schemas) and never construct geography values by hand.
    """
    if target.latitude is not None and target.longitude is not None:
        target.location = to_wkt_point(float(target.latitude), float(target.longitude))
    else:
        target.location = None
