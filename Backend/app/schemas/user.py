import uuid
from datetime import datetime

from pydantic import BaseModel

from app.utils.enums import UserRole


class UserSummary(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    phone: str | None
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None

    model_config = {"from_attributes": True}


class PaginatedUsers(BaseModel):
    items: list[UserSummary]
    total: int
    page: int
    page_size: int


class UserStatusUpdate(BaseModel):
    is_active: bool
