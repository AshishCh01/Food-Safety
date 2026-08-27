import hashlib
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.complaint import Complaint
from app.models.evidence import Evidence
from app.repositories import evidence_repository
from app.schemas.evidence import EvidenceRead
from app.services import storage_service
from app.utils.enums import ComplaintStatus
from app.utils.exceptions import ConflictError
from app.utils.geo import validate_coordinates
from app.utils.validators import validate_evidence_file

# Complaints in these states are no longer open for new evidence.
LOCKED_STATUSES = {
    ComplaintStatus.REJECTED,
    ComplaintStatus.DUPLICATE,
    ComplaintStatus.RESOLVED,
    ComplaintStatus.CLOSED,
    ComplaintStatus.CANCELLED,
}


def upload_evidence(
    db: Session,
    *,
    complaint: Complaint,
    uploaded_by_user_id: uuid.UUID,
    file_bytes: bytes,
    filename: str,
    content_type: str,
    inspection_id: uuid.UUID | None = None,
    captured_at: datetime | None = None,
    latitude: Decimal | None = None,
    longitude: Decimal | None = None,
) -> Evidence:
    if complaint.status in LOCKED_STATUSES:
        raise ConflictError("Evidence cannot be added to a complaint in this status.")

    validate_evidence_file(filename, content_type, len(file_bytes))
    validate_coordinates(
        float(latitude) if latitude is not None else None,
        float(longitude) if longitude is not None else None,
    )

    settings = get_settings()
    checksum = hashlib.sha256(file_bytes).hexdigest()
    folder = f"inspections/{inspection_id}" if inspection_id else f"evidence/{complaint.id}"
    storage_path = f"{folder}/{uuid.uuid4()}_{filename}"
    storage_service.upload_file(settings.supabase_storage_bucket, storage_path, file_bytes, content_type)

    return evidence_repository.create(
        db,
        complaint_id=complaint.id,
        inspection_id=inspection_id,
        uploaded_by_user_id=uploaded_by_user_id,
        storage_bucket=settings.supabase_storage_bucket,
        storage_path=storage_path,
        file_name=filename,
        file_type=content_type,
        file_size=len(file_bytes),
        checksum=checksum,
        captured_at=captured_at,
        latitude=latitude,
        longitude=longitude,
    )


def list_evidence_with_urls(db: Session, complaint_id: uuid.UUID) -> list[EvidenceRead]:
    items = evidence_repository.list_by_complaint(db, complaint_id)
    return _to_evidence_reads_with_urls(items)


def list_inspection_evidence_with_urls(db: Session, inspection_id: uuid.UUID) -> list[EvidenceRead]:
    items = evidence_repository.list_by_inspection(db, inspection_id)
    return _to_evidence_reads_with_urls(items)


def _to_evidence_reads_with_urls(items: list[Evidence]) -> list[EvidenceRead]:
    results = []
    for item in items:
        download_url = storage_service.create_signed_url(item.storage_bucket, item.storage_path)
        results.append(to_evidence_read(item, download_url=download_url))
    return results


def to_evidence_read(evidence: Evidence, *, download_url: str | None = None) -> EvidenceRead:
    return EvidenceRead(
        id=evidence.id,
        complaint_id=evidence.complaint_id,
        file_name=evidence.file_name,
        file_type=evidence.file_type,
        file_size=evidence.file_size,
        checksum=evidence.checksum,
        captured_at=evidence.captured_at,
        latitude=float(evidence.latitude) if evidence.latitude is not None else None,
        longitude=float(evidence.longitude) if evidence.longitude is not None else None,
        uploaded_by_user_id=evidence.uploaded_by_user_id,
        created_at=evidence.created_at,
        download_url=download_url,
    )
