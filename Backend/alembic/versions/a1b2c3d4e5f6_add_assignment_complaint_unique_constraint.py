"""add unique constraint on assignments.complaint_id

Revision ID: a1b2c3d4e5f6
Revises: 8f1a2c6d4b3e
Create Date: 2026-08-29 00:00:00.000000

A complaint is assigned to exactly one inspector at a time (mirroring the
existing `inspections.complaint_id` unique constraint) - `assignment_service`
and `assignment_repository.get_by_complaint_id` already assume this 1:1
relationship, but without a database-level constraint, two concurrent
`assign_inspector` requests for the same complaint (e.g. two officers acting
on the same district queue at once) could both pass the
`complaint.status != VERIFIED` check before either commits and create two
`assignments` rows for one complaint - `get_by_complaint_id`'s
`scalar_one_or_none()` would then raise `MultipleResultsFound` on every
subsequent read of that complaint's assignment. See docs/SECURITY_AND_RBAC.md
section 5 (defense in depth) and Phase 12 hardening notes in
docs/DEVELOPMENT_ROADMAP.md.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '8f1a2c6d4b3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint('uq_assignments_complaint_id', 'assignments', ['complaint_id'])


def downgrade() -> None:
    op.drop_constraint('uq_assignments_complaint_id', 'assignments', type_='unique')
