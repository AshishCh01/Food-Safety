import uuid

from sqlalchemy import func, select
from sqlalchemy import update as sa_update
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.utils.enums import NotificationType


def create(
    db: Session,
    *,
    user_id: uuid.UUID,
    type: NotificationType,
    title: str,
    message: str,
    entity_type: str,
    entity_id: uuid.UUID,
) -> Notification:
    """Writes a notification within the caller's transaction (flush only,
    never commits) so it lands atomically with the workflow action that
    triggered it - mirrors app.repositories.audit_log_repository.record."""
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    db.add(notification)
    db.flush()
    return notification


def get_by_id(db: Session, notification_id: uuid.UUID) -> Notification | None:
    return db.get(Notification, notification_id)


def list_by_user(
    db: Session,
    user_id: uuid.UUID,
    *,
    is_read: bool | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Notification], int]:
    stmt = select(Notification).where(Notification.user_id == user_id)
    if is_read is not None:
        stmt = stmt.where(Notification.is_read == is_read)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    stmt = stmt.order_by(Notification.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = list(db.execute(stmt).scalars().all())
    return items, total


def count_unread(db: Session, user_id: uuid.UUID) -> int:
    stmt = select(func.count()).select_from(Notification).where(
        Notification.user_id == user_id, Notification.is_read.is_(False)
    )
    return db.execute(stmt).scalar_one()


def mark_read(db: Session, notification: Notification) -> Notification:
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_read(db: Session, user_id: uuid.UUID) -> int:
    stmt = (
        sa_update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    result = db.execute(stmt)
    db.commit()
    return result.rowcount or 0
