import uuid
from datetime import datetime

from pydantic import BaseModel


class AuditLogRead(BaseModel):
    id: uuid.UUID
    actor_user_id: uuid.UUID
    actor_name: str
    action: str
    entity_type: str
    entity_id: uuid.UUID
    details: dict | None
    created_at: datetime


class PaginatedAuditLogs(BaseModel):
    items: list[AuditLogRead]
    total: int
    page: int
    page_size: int
