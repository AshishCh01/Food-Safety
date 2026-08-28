import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.utils.enums import RagDocumentStatus, RagDocumentType


class RagDocumentCreate(BaseModel):
    """Multipart form metadata accompanying an uploaded knowledge-base file
    (see docs/RAG_ARCHITECTURE.md section 5). The file itself is a separate
    `UploadFile` form field, not part of this model."""

    title: str = Field(min_length=1, max_length=500)
    source_organization: str | None = Field(default=None, max_length=255)
    document_type: RagDocumentType
    version: str | None = Field(default=None, max_length=50)
    effective_date: date | None = None
    source_url: str | None = Field(default=None, max_length=1000)
    business_type: str | None = Field(default=None, max_length=100)
    jurisdiction: str = Field(default="India", max_length=100)


class RagDocumentRead(BaseModel):
    id: uuid.UUID
    title: str
    source_organization: str | None
    document_type: RagDocumentType
    version: str | None
    effective_date: date | None
    source_url: str | None
    original_filename: str
    file_type: str
    business_type: str | None
    jurisdiction: str
    status: RagDocumentStatus
    is_active: bool
    error_message: str | None
    chunk_count: int
    created_at: datetime
    updated_at: datetime


class PaginatedRagDocuments(BaseModel):
    items: list[RagDocumentRead]
    total: int
    page: int
    page_size: int


class RagCitation(BaseModel):
    document_id: uuid.UUID
    title: str
    source_organization: str | None
    page_number: int | None
    section_title: str | None
