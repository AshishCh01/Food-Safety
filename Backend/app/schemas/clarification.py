import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ClarificationRespondRequest(BaseModel):
    response_message: str = Field(min_length=10, max_length=5000)


class ClarificationRead(BaseModel):
    id: uuid.UUID
    complaint_id: uuid.UUID
    officer_message: str | None   # from ComplaintStatusHistory.reason
    requested_at: datetime        # ComplaintClarification.created_at
    response_message: str | None
    responded_at: datetime | None

    class Config:
        from_attributes = True