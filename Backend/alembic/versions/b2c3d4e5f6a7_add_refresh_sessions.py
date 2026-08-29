"""add refresh_sessions table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-29 00:00:00.000000

Adds server-side, revocable refresh-token session storage
(docs/SECURITY_AND_RBAC.md section 18 - stateless refresh tokens could not
previously be revoked). Only a SHA-256 hash of each opaque refresh token is
stored, never the token itself. See app/models/refresh_session.py and
app/services/auth_service.py for the rotation/reuse-detection design.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'refresh_sessions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('family_id', sa.Uuid(), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_reason', sa.String(length=50), nullable=True),
        sa.Column('replaced_by_id', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['replaced_by_id'], ['refresh_sessions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash', name='uq_refresh_sessions_token_hash'),
    )
    op.create_index('ix_refresh_sessions_user_id', 'refresh_sessions', ['user_id'], unique=False)
    op.create_index('ix_refresh_sessions_family_id', 'refresh_sessions', ['family_id'], unique=False)
    op.create_index('ix_refresh_sessions_expires_at', 'refresh_sessions', ['expires_at'], unique=False)
    op.create_index('ix_refresh_sessions_token_hash', 'refresh_sessions', ['token_hash'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_refresh_sessions_token_hash', table_name='refresh_sessions')
    op.drop_index('ix_refresh_sessions_expires_at', table_name='refresh_sessions')
    op.drop_index('ix_refresh_sessions_family_id', table_name='refresh_sessions')
    op.drop_index('ix_refresh_sessions_user_id', table_name='refresh_sessions')
    op.drop_table('refresh_sessions')
