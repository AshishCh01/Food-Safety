import uuid

from pydantic import BaseModel


class ComplaintSubcategoryRead(BaseModel):
    id: uuid.UUID
    key: str
    name: str
    description: str | None
    is_active: bool

class ComplaintCategoryRead(BaseModel):
    id: uuid.UUID
    key: str
    name: str
    description: str | None
    is_active: bool
    subcategories: list[ComplaintSubcategoryRead] = []
