"""add postgis and location columns

Revision ID: 014114ea0cea
Revises: 30824dc06f71
Create Date: 2026-08-27 16:00:00.000000

"""
from typing import Sequence, Union

import geoalchemy2
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '014114ea0cea'
down_revision: Union[str, None] = '30824dc06f71'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')

    # District centroid (approximate HQ coordinates, see
    # scripts/maharashtra_geography.py) used for nearest-district resolution
    # of a reported complaint location. Plain numeric columns - no PostGIS
    # dependency needed for a 36-row nearest-neighbour lookup.
    op.add_column('districts', sa.Column('centroid_latitude', sa.Numeric(precision=9, scale=6), nullable=True))
    op.add_column('districts', sa.Column('centroid_longitude', sa.Numeric(precision=9, scale=6), nullable=True))

    # PostGIS geography columns, kept in sync with the existing
    # latitude/longitude columns by a SQLAlchemy event listener (see
    # app/core/geo_types.py) so application code never constructs geography
    # values directly.
    op.add_column(
        'businesses',
        sa.Column('location', geoalchemy2.types.Geography(geometry_type='POINT', srid=4326, from_text='ST_GeogFromText', name='geography'), nullable=True),
    )
    op.add_column(
        'complaints',
        sa.Column('location', geoalchemy2.types.Geography(geometry_type='POINT', srid=4326, from_text='ST_GeogFromText', name='geography'), nullable=True),
    )

    # Backfill from existing latitude/longitude data before indexing.
    op.execute(
        "UPDATE businesses SET location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography "
        "WHERE latitude IS NOT NULL AND longitude IS NOT NULL"
    )
    op.execute(
        "UPDATE complaints SET location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography "
        "WHERE latitude IS NOT NULL AND longitude IS NOT NULL"
    )

    op.execute('CREATE INDEX ix_businesses_location ON businesses USING GIST (location)')
    op.execute('CREATE INDEX ix_complaints_location ON complaints USING GIST (location)')


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS ix_complaints_location')
    op.execute('DROP INDEX IF EXISTS ix_businesses_location')
    op.drop_column('complaints', 'location')
    op.drop_column('businesses', 'location')
    op.drop_column('districts', 'centroid_longitude')
    op.drop_column('districts', 'centroid_latitude')

    # The postgis extension is left installed on downgrade - other objects
    # in the database may depend on it, and dropping/recreating it is not
    # something a routine migration rollback should do.
