import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.legal_action import LegalAction


def create(db: Session, **kwargs) -> LegalAction:
    action = LegalAction(**kwargs)
    db.add(action)
    db.flush()
    return action


def get_by_id(db: Session, action_id: uuid.UUID) -> LegalAction | None:
    return db.get(LegalAction, action_id)


def list_by_complaint(db: Session, complaint_id: uuid.UUID) -> list[LegalAction]:
    return list(
        db.execute(
            select(LegalAction).where(LegalAction.complaint_id == complaint_id).order_by(LegalAction.created_at)
        ).scalars()
    )