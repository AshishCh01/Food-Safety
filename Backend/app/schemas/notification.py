import uuid
from datetime import datetime

from pydantic import BaseModel

from app.utils.enums import NotificationType


class NotificationRead(BaseModel):
    id: uuid.UUID
    type: NotificationType
    title: str
    message: str
    entity_type: str
    entity_id: uuid.UUID
    is_read: bool
    created_at: datetime


class PaginatedNotifications(BaseModel):
    items: list[NotificationRead]
    total: int
    page: int
    page_size: int


class UnreadCountRead(BaseModel):
    unread_count: int


class MarkAllReadResponse(BaseModel):
    marked_count: int
