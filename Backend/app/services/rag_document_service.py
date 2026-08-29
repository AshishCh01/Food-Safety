import hashlib
import uuid

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.rag_document import RagDocument
from app.models.user import User
from app.rag import ingestion
from app.repositories import audit_log_repository, rag_document_repository
from app.schemas.rag import RagDocumentCreate, RagDocumentRead
from app.services import storage_service
from app.utils.enums import RagDocumentStatus
from app.utils.exceptions import RagDocumentDuplicateError, RagDocumentNotFoundError
from app.utils.validators import validate_rag_document_file


def upload_document(
    db: Session,
    uploaded_by: User,
    payload: RagDocumentCreate,
    *,
    file_bytes: bytes,
    filename: str,
    content_type: str,
) -> RagDocument:
    safe_filename = validate_rag_document_file(filename, content_type, len(file_bytes), file_bytes[:16])

    checksum = hashlib.sha256(file_bytes).hexdigest()
    if rag_document_repository.get_by_checksum(db, checksum) is not None:
        raise RagDocumentDuplicateError()

    settings = get_settings()
    storage_path = f"{payload.document_type.value}/{uuid.uuid4()}_{safe_filename}"
    storage_service.upload_file(settings.rag_storage_bucket, storage_path, file_bytes, content_type)

    document = RagDocument(
        title=payload.title,
        source_organization=payload.source_organization,
        document_type=payload.document_type,
        version=payload.version,
        effective_date=payload.effective_date,
        source_url=payload.source_url,
        storage_path=storage_path,
        original_filename=safe_filename,
        file_type=content_type,
        checksum=checksum,
        business_type=payload.business_type,
        jurisdiction=payload.jurisdiction,
        status=RagDocumentStatus.PENDING,
        uploaded_by_user_id=uploaded_by.id,
    )
    document = rag_document_repository.create(db, document)

    audit_log_repository.record(
        db,
        actor_user_id=uploaded_by.id,
        action="rag_document_uploaded",
        entity_type="rag_document",
        entity_id=document.id,
        details={"title": document.title, "document_type": document.document_type.value},
    )
    db.commit()
    return document


def get_document(db: Session, document_id: uuid.UUID) -> RagDocument:
    document = rag_document_repository.get_by_id(db, document_id)
    if document is None:
        raise RagDocumentNotFoundError()
    return document


def run_ingestion(db: Session, document: RagDocument, *, actor_user_id: uuid.UUID) -> RagDocument:
    settings = get_settings()
    file_bytes = storage_service.download_file(settings.rag_storage_bucket, document.storage_path)
    document = ingestion.ingest_document(db, document, file_bytes)

    audit_log_repository.record(
        db,
        actor_user_id=actor_user_id,
        action="rag_document_ingested",
        entity_type="rag_document",
        entity_id=document.id,
        details={"status": document.status.value, "chunk_count": document.chunk_count},
    )
    db.commit()
    return document


def deactivate_document(db: Session, document: RagDocument, *, actor_user_id: uuid.UUID) -> RagDocument:
    document.is_active = False
    document = rag_document_repository.update(db, document)

    audit_log_repository.record(
        db,
        actor_user_id=actor_user_id,
        action="rag_document_deactivated",
        entity_type="rag_document",
        entity_id=document.id,
        details=None,
    )
    db.commit()
    return document


def to_document_read(document: RagDocument) -> RagDocumentRead:
    return RagDocumentRead(
        id=document.id,
        title=document.title,
        source_organization=document.source_organization,
        document_type=document.document_type,
        version=document.version,
        effective_date=document.effective_date,
        source_url=document.source_url,
        original_filename=document.original_filename,
        file_type=document.file_type,
        business_type=document.business_type,
        jurisdiction=document.jurisdiction,
        status=document.status,
        is_active=document.is_active,
        error_message=document.error_message,
        chunk_count=document.chunk_count,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )
