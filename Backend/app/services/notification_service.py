import uuid

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.repositories import notification_repository
from app.schemas.notification import NotificationRead
from app.utils.exceptions import NotificationNotFoundError


def list_for_user(
    db: Session,
    user_id: uuid.UUID,
    *,
    is_read: bool | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Notification], int]:
    return notification_repository.list_by_user(db, user_id, is_read=is_read, page=page, page_size=page_size)


def unread_count(db: Session, user_id: uuid.UUID) -> int:
    return notification_repository.count_unread(db, user_id)


def mark_read(db: Session, user_id: uuid.UUID, notification_id: uuid.UUID) -> Notification:
    notification = notification_repository.get_by_id(db, notification_id)
    if notification is None or notification.user_id != user_id:
        raise NotificationNotFoundError()
    return notification_repository.mark_read(db, notification)


def mark_all_read(db: Session, user_id: uuid.UUID) -> int:
    return notification_repository.mark_all_read(db, user_id)


def to_notification_read(notification: Notification) -> NotificationRead:
    return NotificationRead(
        id=notification.id,
        type=notification.type,
        title=notification.title,
        message=notification.message,
        entity_type=notification.entity_type,
        entity_id=notification.entity_id,
        is_read=notification.is_read,
        created_at=notification.created_at,
    )
