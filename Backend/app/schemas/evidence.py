import uuid
from datetime import datetime

from pydantic import BaseModel


class EvidenceRead(BaseModel):
    id: uuid.UUID
    complaint_id: uuid.UUID
    file_name: str
    file_type: str
    file_size: int
    checksum: str
    captured_at: datetime | None
    latitude: float | None
    longitude: float | None
    uploaded_by_user_id: uuid.UUID
    created_at: datetime
    download_url: str | None = None
