import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evidence import Evidence


def get_by_id(db: Session, evidence_id: uuid.UUID) -> Evidence | None:
    return db.get(Evidence, evidence_id)


def list_by_complaint(db: Session, complaint_id: uuid.UUID) -> list[Evidence]:
    stmt = select(Evidence).where(Evidence.complaint_id == complaint_id).order_by(Evidence.created_at)
    return list(db.execute(stmt).scalars().all())


def list_by_inspection(db: Session, inspection_id: uuid.UUID) -> list[Evidence]:
    stmt = select(Evidence).where(Evidence.inspection_id == inspection_id).order_by(Evidence.created_at)
    return list(db.execute(stmt).scalars().all())


def create(
    db: Session,
    *,
    complaint_id: uuid.UUID,
    uploaded_by_user_id: uuid.UUID,
    storage_bucket: str,
    storage_path: str,
    file_name: str,
    file_type: str,
    file_size: int,
    checksum: str,
    inspection_id: uuid.UUID | None = None,
    captured_at: datetime | None = None,
    latitude: Decimal | None = None,
    longitude: Decimal | None = None,
) -> Evidence:
    evidence = Evidence(
        complaint_id=complaint_id,
        inspection_id=inspection_id,
        uploaded_by_user_id=uploaded_by_user_id,
        storage_bucket=storage_bucket,
        storage_path=storage_path,
        file_name=file_name,
        file_type=file_type,
        file_size=file_size,
        checksum=checksum,
        captured_at=captured_at,
        latitude=latitude,
        longitude=longitude,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence
