import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.complaint_clarification import ComplaintClarification


def create(db: Session, **kwargs) -> ComplaintClarification:
    clarification = ComplaintClarification(**kwargs)
    db.add(clarification)
    db.flush()
    return clarification


def get_latest_for_complaint(db: Session, complaint_id: uuid.UUID) -> ComplaintClarification | None:
    return db.execute(
        select(ComplaintClarification)
        .where(
            ComplaintClarification.complaint_id == complaint_id,
            ComplaintClarification.response_message.is_(None),
        )
        .order_by(ComplaintClarification.created_at.desc())
    ).scalar_one_or_none()


def record_response(
    db: Session,
    clarification: ComplaintClarification,
    response_message: str,
    responded_by_user_id: uuid.UUID,
) -> ComplaintClarification:
    clarification.response_message = response_message
    clarification.responded_at = datetime.now(timezone.utc)
    clarification.responded_by_user_id = responded_by_user_id
    db.flush()
    return clarification