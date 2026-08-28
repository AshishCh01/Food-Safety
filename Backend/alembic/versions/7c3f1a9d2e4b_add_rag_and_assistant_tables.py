"""add rag and assistant tables

Revision ID: 7c3f1a9d2e4b
Revises: 09b78bb3d711
Create Date: 2026-08-27 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '7c3f1a9d2e4b'
down_revision: Union[str, None] = '09b78bb3d711'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Must match Settings.gemini_embedding_dimensions (app/core/config.py). A future
# embedding-model change that alters this requires a new migration that rebuilds
# the column and re-ingests the knowledge base (see docs/RAG_ARCHITECTURE.md
# section 7 - never mix incompatible vector dimensions in one collection).
EMBEDDING_DIM = 768


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    op.create_table(
        'rag_documents',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('source_organization', sa.String(length=255), nullable=True),
        sa.Column(
            'document_type',
            sa.Enum(
                'law', 'regulation', 'inspection_guideline', 'hygiene_guideline', 'sampling_procedure',
                'recall_procedure', 'licensing', 'department_sop', 'other', name='rag_document_type',
            ),
            nullable=False,
        ),
        sa.Column('version', sa.String(length=50), nullable=True),
        sa.Column('effective_date', sa.Date(), nullable=True),
        sa.Column('source_url', sa.String(length=1000), nullable=True),
        sa.Column('storage_path', sa.String(length=1000), nullable=False),
        sa.Column('original_filename', sa.String(length=500), nullable=False),
        sa.Column('file_type', sa.String(length=100), nullable=False),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column('business_type', sa.String(length=100), nullable=True),
        sa.Column('jurisdiction', sa.String(length=100), nullable=False),
        sa.Column(
            'status',
            sa.Enum('pending', 'ingested', 'failed', 'superseded', 'deactivated', name='rag_document_status'),
            nullable=False,
        ),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('superseded_by_document_id', sa.Uuid(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('chunk_count', sa.Integer(), nullable=False),
        sa.Column('uploaded_by_user_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'),
            onupdate=sa.text('now()'), nullable=False,
        ),
        sa.ForeignKeyConstraint(['superseded_by_document_id'], ['rag_documents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['uploaded_by_user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_rag_documents_document_type'), 'rag_documents', ['document_type'], unique=False)
    op.create_index(op.f('ix_rag_documents_checksum'), 'rag_documents', ['checksum'], unique=False)

    op.create_table(
        'rag_document_chunks',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('document_id', sa.Uuid(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('section_title', sa.String(length=500), nullable=True),
        sa.Column('heading_path', sa.String(length=1000), nullable=True),
        sa.Column('chunk_metadata', sa.JSON(), nullable=False),
        sa.Column('embedding', Vector(EMBEDDING_DIM), nullable=False),
        sa.Column('embedding_model', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['rag_documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_rag_document_chunks_document_id'), 'rag_document_chunks', ['document_id'], unique=False)
    op.create_index(
        'ix_rag_chunks_document_chunk_index', 'rag_document_chunks', ['document_id', 'chunk_index'], unique=False
    )
    op.execute(
        'CREATE INDEX ix_rag_document_chunks_embedding ON rag_document_chunks '
        'USING hnsw (embedding vector_cosine_ops)'
    )

    op.create_table(
        'assistant_conversations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('inspector_staff_id', sa.Uuid(), nullable=False),
        sa.Column('inspection_id', sa.Uuid(), nullable=True),
        sa.Column('complaint_id', sa.Uuid(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'),
            onupdate=sa.text('now()'), nullable=False,
        ),
        sa.ForeignKeyConstraint(['inspector_staff_id'], ['staff_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['inspection_id'], ['inspections.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['complaint_id'], ['complaints.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_assistant_conversations_inspector_staff_id'), 'assistant_conversations', ['inspector_staff_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_assistant_conversations_inspection_id'), 'assistant_conversations', ['inspection_id'], unique=False
    )

    op.create_table(
        'assistant_messages',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('conversation_id', sa.Uuid(), nullable=False),
        sa.Column('role', sa.Enum('user', 'assistant', name='assistant_message_role'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('citations', sa.JSON(), nullable=True),
        sa.Column('application_data_used', sa.JSON(), nullable=True),
        sa.Column('is_uncertain', sa.Boolean(), nullable=False),
        sa.Column('uncertainty_reason', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['assistant_conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_assistant_messages_conversation_id'), 'assistant_messages', ['conversation_id'], unique=False
    )
    op.create_index(
        'ix_assistant_messages_conversation_created', 'assistant_messages', ['conversation_id', 'created_at'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_assistant_messages_conversation_created', table_name='assistant_messages')
    op.drop_index(op.f('ix_assistant_messages_conversation_id'), table_name='assistant_messages')
    op.drop_table('assistant_messages')

    op.drop_index(op.f('ix_assistant_conversations_inspection_id'), table_name='assistant_conversations')
    op.drop_index(op.f('ix_assistant_conversations_inspector_staff_id'), table_name='assistant_conversations')
    op.drop_table('assistant_conversations')

    op.execute('DROP INDEX IF EXISTS ix_rag_document_chunks_embedding')
    op.drop_index('ix_rag_chunks_document_chunk_index', table_name='rag_document_chunks')
    op.drop_index(op.f('ix_rag_document_chunks_document_id'), table_name='rag_document_chunks')
    op.drop_table('rag_document_chunks')

    op.drop_index(op.f('ix_rag_documents_checksum'), table_name='rag_documents')
    op.drop_index(op.f('ix_rag_documents_document_type'), table_name='rag_documents')
    op.drop_table('rag_documents')

    # The `vector` extension is left installed on downgrade, same rationale as
    # the existing PostGIS migration - other objects may depend on it.
    bind = op.get_bind()
    sa.Enum(name='assistant_message_role').drop(bind, checkfirst=True)
    sa.Enum(name='rag_document_status').drop(bind, checkfirst=True)
    sa.Enum(name='rag_document_type').drop(bind, checkfirst=True)
