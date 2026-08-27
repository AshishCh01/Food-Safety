import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.business import BusinessInput, BusinessRead
from app.utils.enums import ComplaintPriority, ComplaintStatus


class ComplaintCreateRequest(BaseModel):
    category_id: uuid.UUID
    district_id: uuid.UUID
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=5000)
    priority: ComplaintPriority = ComplaintPriority.MEDIUM
    latitude: float | None = None
    longitude: float | None = None
    address_line: str | None = Field(default=None, max_length=500)
    reported_at: datetime | None = None
    business: BusinessInput


class ComplaintRead(BaseModel):
    id: uuid.UUID
    complaint_number: str
    title: str
    description: str
    status: ComplaintStatus
    priority: ComplaintPriority
    category_id: uuid.UUID
    category_name: str
    district_id: uuid.UUID
    district_name: str
    business: BusinessRead | None
    latitude: float | None
    longitude: float | None
    address_line: str | None
    reported_at: datetime
    verified_at: datetime | None
    resolved_at: datetime | None
    submitted_by_user_id: uuid.UUID
    submitted_by_name: str
    created_at: datetime
    updated_at: datetime


class ComplaintSummary(BaseModel):
    id: uuid.UUID
    complaint_number: str
    title: str
    category_name: str
    status: ComplaintStatus
    priority: ComplaintPriority
    district_name: str
    created_at: datetime


class PaginatedComplaints(BaseModel):
    items: list[ComplaintSummary]
    total: int
    page: int
    page_size: int


class ComplaintStatusUpdateRequest(BaseModel):
    status: ComplaintStatus
    reason: str | None = Field(default=None, max_length=1000)


class ComplaintMapMarker(BaseModel):
    id: uuid.UUID
    complaint_number: str
    title: str
    status: ComplaintStatus
    priority: ComplaintPriority
    category_id: uuid.UUID
    category_name: str
    latitude: float
    longitude: float
    business_name: str | None
    created_at: datetime


class ComplaintMapData(BaseModel):
    items: list[ComplaintMapMarker]
    total: int
