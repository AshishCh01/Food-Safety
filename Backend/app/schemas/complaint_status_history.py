import uuid
from datetime import datetime

from pydantic import BaseModel

from app.utils.enums import ComplaintStatus


class ComplaintStatusHistoryRead(BaseModel):
    id: uuid.UUID
    old_status: ComplaintStatus | None
    new_status: ComplaintStatus
    changed_by_user_id: uuid.UUID
    changed_by_name: str
    reason: str | None
    created_at: datetime
