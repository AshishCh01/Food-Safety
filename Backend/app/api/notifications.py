import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.notification import MarkAllReadResponse, NotificationRead, PaginatedNotifications, UnreadCountRead
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=PaginatedNotifications)
def list_notifications(
    is_read: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedNotifications:
    """Lists the current user's own notifications. Scope is always derived
    from the authenticated user - there is no way to request another user's
    notifications."""
    items, total = notification_service.list_for_user(
        db, current_user.id, is_read=is_read, page=page, page_size=page_size
    )
    return PaginatedNotifications(
        items=[notification_service.to_notification_read(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/unread-count", response_model=UnreadCountRead)
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UnreadCountRead:
    return UnreadCountRead(unread_count=notification_service.unread_count(db, current_user.id))


@router.patch("/{notification_id}/read", response_model=NotificationRead)
def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationRead:
    notification = notification_service.mark_read(db, current_user.id, notification_id)
    return notification_service.to_notification_read(notification)


@router.post("/read-all", response_model=MarkAllReadResponse)
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MarkAllReadResponse:
    marked_count = notification_service.mark_all_read(db, current_user.id)
    return MarkAllReadResponse(marked_count=marked_count)
