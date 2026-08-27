import uuid

from pydantic import BaseModel


class DistrictRead(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    division_id: uuid.UUID
    division_name: str
    centroid_latitude: float | None = None
    centroid_longitude: float | None = None
    is_active: bool
