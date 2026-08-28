import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.rag_document import RagDocument
from app.utils.enums import RagDocumentStatus, RagDocumentType


def create(db: Session, document: RagDocument) -> RagDocument:
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def get_by_id(db: Session, document_id: uuid.UUID) -> RagDocument | None:
    return db.get(RagDocument, document_id)


def get_by_checksum(db: Session, checksum: str) -> RagDocument | None:
    """Used for upload-time duplicate detection (docs/RAG_ARCHITECTURE.md
    section 11) - only considers documents that are not already superseded/
    deactivated, so a deliberately replaced document can be re-uploaded."""
    stmt = select(RagDocument).where(
        RagDocument.checksum == checksum,
        RagDocument.status.in_([RagDocumentStatus.PENDING, RagDocumentStatus.INGESTED, RagDocumentStatus.FAILED]),
        RagDocument.is_active.is_(True),
    )
    return db.execute(stmt).scalars().first()


def list_documents(
    db: Session,
    *,
    status: RagDocumentStatus | None = None,
    document_type: RagDocumentType | None = None,
    is_active: bool | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[RagDocument], int]:
    stmt = select(RagDocument)
    if status is not None:
        stmt = stmt.where(RagDocument.status == status)
    if document_type is not None:
        stmt = stmt.where(RagDocument.document_type == document_type)
    if is_active is not None:
        stmt = stmt.where(RagDocument.is_active == is_active)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    stmt = stmt.order_by(RagDocument.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = list(db.execute(stmt).scalars().all())
    return items, total


def update(db: Session, document: RagDocument) -> RagDocument:
    db.add(document)
    db.commit()
    db.refresh(document)
    return document
