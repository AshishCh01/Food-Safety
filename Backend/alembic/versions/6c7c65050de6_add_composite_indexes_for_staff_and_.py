"""add composite indexes for staff and inspector status queries

Revision ID: 6c7c65050de6
Revises: b2c3d4e5f6a7
Create Date: 2026-09-01 15:33:10.404200

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6c7c65050de6'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        'ix_assignments_staff_status', 'assignments', ['assigned_to_staff_id', 'status'], unique=False
    )
    op.create_index(
        'ix_inspections_inspector_status', 'inspections', ['inspector_id', 'inspection_status'], unique=False
    )


def downgrade() -> None:
    op.drop_index('ix_inspections_inspector_status', table_name='inspections')
    op.drop_index('ix_assignments_staff_status', table_name='assignments')
