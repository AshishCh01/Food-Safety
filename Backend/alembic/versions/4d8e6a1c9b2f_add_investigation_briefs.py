"""add investigation briefs

Revision ID: 4d8e6a1c9b2f
Revises: 7c3f1a9d2e4b
Create Date: 2026-08-27 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d8e6a1c9b2f'
down_revision: Union[str, None] = '7c3f1a9d2e4b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'investigation_briefs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('complaint_id', sa.Uuid(), nullable=False),
        sa.Column('requested_by_user_id', sa.Uuid(), nullable=False),
        sa.Column('status', sa.Enum('completed', 'failed', name='investigation_status'), nullable=False),
        sa.Column('model_used', sa.String(length=100), nullable=False),
        sa.Column('case_summary', sa.Text(), nullable=True),
        sa.Column('relevant_evidence', sa.JSON(), nullable=True),
        sa.Column('business_history', sa.JSON(), nullable=True),
        sa.Column('complaint_patterns', sa.JSON(), nullable=True),
        sa.Column('regulatory_guidance', sa.JSON(), nullable=True),
        sa.Column('risk_indicators', sa.JSON(), nullable=True),
        sa.Column('missing_information', sa.JSON(), nullable=True),
        sa.Column('suggested_actions', sa.JSON(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('is_uncertain', sa.Boolean(), nullable=False),
        sa.Column('uncertainty_reasons', sa.JSON(), nullable=True),
        sa.Column('error_code', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['complaint_id'], ['complaints.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['requested_by_user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_investigation_briefs_complaint_id'), 'investigation_briefs', ['complaint_id'], unique=False
    )
    op.create_index(
        'ix_investigation_briefs_complaint_created', 'investigation_briefs', ['complaint_id', 'created_at'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_investigation_briefs_complaint_created', table_name='investigation_briefs')
    op.drop_index(op.f('ix_investigation_briefs_complaint_id'), table_name='investigation_briefs')
    op.drop_table('investigation_briefs')

    bind = op.get_bind()
    sa.Enum(name='investigation_status').drop(bind, checkfirst=True)
