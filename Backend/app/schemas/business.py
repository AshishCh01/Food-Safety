import uuid

from pydantic import BaseModel, Field


class BusinessInput(BaseModel):
    business_name: str = Field(min_length=1, max_length=255)
    business_type: str | None = Field(default=None, max_length=100)
    license_number: str | None = Field(default=None, max_length=100)
    address: str = Field(min_length=1, max_length=500)
    contact_phone: str | None = Field(default=None, max_length=20)
    latitude: float | None = None
    longitude: float | None = None


class BusinessRead(BaseModel):
    id: uuid.UUID
    business_name: str
    business_type: str | None
    license_number: str | None
    address: str
    district_id: uuid.UUID
    latitude: float | None
    longitude: float | None
    contact_phone: str | None
    is_active: bool
