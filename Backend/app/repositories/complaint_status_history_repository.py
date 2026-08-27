import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.complaint_status_history import ComplaintStatusHistory
from app.utils.enums import ComplaintStatus


def create(
    db: Session,
    *,
    complaint_id: uuid.UUID,
    old_status: ComplaintStatus | None,
    new_status: ComplaintStatus,
    changed_by_user_id: uuid.UUID,
    reason: str | None = None,
) -> ComplaintStatusHistory:
    history = ComplaintStatusHistory(
        complaint_id=complaint_id,
        old_status=old_status,
        new_status=new_status,
        changed_by_user_id=changed_by_user_id,
        reason=reason,
    )
    db.add(history)
    db.flush()
    return history


def list_by_complaint(db: Session, complaint_id: uuid.UUID) -> list[ComplaintStatusHistory]:
    stmt = (
        select(ComplaintStatusHistory)
        .where(ComplaintStatusHistory.complaint_id == complaint_id)
        .options(joinedload(ComplaintStatusHistory.changed_by))
        .order_by(ComplaintStatusHistory.created_at)
    )
    return list(db.execute(stmt).scalars().all())
