import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.investigation_brief import InvestigationBrief


def create(db: Session, brief: InvestigationBrief) -> InvestigationBrief:
    db.add(brief)
    db.flush()
    return brief


def get_latest_by_complaint(db: Session, complaint_id: uuid.UUID) -> InvestigationBrief | None:
    stmt = (
        select(InvestigationBrief)
        .where(InvestigationBrief.complaint_id == complaint_id)
        .order_by(InvestigationBrief.created_at.desc())
        .limit(1)
    )
    return db.execute(stmt).scalars().first()


def list_by_complaint(db: Session, complaint_id: uuid.UUID) -> list[InvestigationBrief]:
    stmt = (
        select(InvestigationBrief)
        .where(InvestigationBrief.complaint_id == complaint_id)
        .order_by(InvestigationBrief.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())
