import uuid

from pydantic import BaseModel


class ComplaintCategoryRead(BaseModel):
    id: uuid.UUID
    key: str
    name: str
    description: str | None
    is_active: bool
