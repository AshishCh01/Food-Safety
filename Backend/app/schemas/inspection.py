import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.utils.enums import FindingSeverity, InspectionStatus


class InspectionCreateRequest(BaseModel):
    complaint_id: uuid.UUID
    scheduled_at: datetime | None = None


class InspectionUpdateRequest(BaseModel):
    scheduled_at: datetime | None = None
    summary: str | None = Field(default=None, max_length=5000)
    action_recommended: str | None = Field(default=None, max_length=2000)
    # The only client-driven status transition through this endpoint - moving
    # to "completed" has its own dedicated endpoint/preconditions.
    status: Literal["in_progress"] | None = None


class InspectionCompleteRequest(BaseModel):
    summary: str = Field(min_length=1, max_length=5000)
    action_recommended: str = Field(min_length=1, max_length=2000)


class InspectionFindingCreateRequest(BaseModel):
    check_code: str = Field(min_length=1, max_length=50)
    finding: str = Field(min_length=1, max_length=2000)
    severity: FindingSeverity
    compliant: bool
    notes: str | None = Field(default=None, max_length=2000)
    corrective_action: str | None = Field(default=None, max_length=2000)


class InspectionFindingRead(BaseModel):
    id: uuid.UUID
    inspection_id: uuid.UUID
    check_code: str
    finding: str
    severity: FindingSeverity
    compliant: bool
    notes: str | None
    corrective_action: str | None
    created_at: datetime


class InspectionRead(BaseModel):
    id: uuid.UUID
    complaint_id: uuid.UUID
    complaint_number: str
    inspector_staff_id: uuid.UUID
    inspector_name: str
    scheduled_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    inspection_status: InspectionStatus
    summary: str | None
    action_recommended: str | None
    findings: list[InspectionFindingRead]
    created_at: datetime
    updated_at: datetime


class InspectionSummary(BaseModel):
    id: uuid.UUID
    complaint_id: uuid.UUID
    complaint_number: str
    inspection_status: InspectionStatus
    scheduled_at: datetime | None
    completed_at: datetime | None


class PaginatedInspections(BaseModel):
    items: list[InspectionSummary]
    total: int
    page: int
    page_size: int
