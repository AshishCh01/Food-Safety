import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.complaint_triage import ComplaintTriage

_EAGER_OPTIONS = (joinedload(ComplaintTriage.suggested_category),)


def create(db: Session, triage: ComplaintTriage) -> ComplaintTriage:
    db.add(triage)
    db.flush()
    return triage


def get_latest_by_complaint(db: Session, complaint_id: uuid.UUID) -> ComplaintTriage | None:
    stmt = (
        select(ComplaintTriage)
        .where(ComplaintTriage.complaint_id == complaint_id)
        .options(*_EAGER_OPTIONS)
        .order_by(ComplaintTriage.created_at.desc())
        .limit(1)
    )
    return db.execute(stmt).scalars().first()


def list_by_complaint(db: Session, complaint_id: uuid.UUID) -> list[ComplaintTriage]:
    stmt = (
        select(ComplaintTriage)
        .where(ComplaintTriage.complaint_id == complaint_id)
        .options(*_EAGER_OPTIONS)
        .order_by(ComplaintTriage.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())
