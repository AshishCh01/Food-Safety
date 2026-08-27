import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.complaint import ComplaintRead
from app.schemas.inspection import InspectionRead
from app.utils.enums import AssignmentStatus


class AssignmentCreateRequest(BaseModel):
    inspector_staff_id: uuid.UUID
    due_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=1000)


class AssignmentSummary(BaseModel):
    id: uuid.UUID
    complaint_id: uuid.UUID
    complaint_number: str
    complaint_title: str
    inspector_staff_id: uuid.UUID
    inspector_name: str
    status: AssignmentStatus
    assigned_at: datetime
    due_at: datetime | None


class AssignmentRead(AssignmentSummary):
    assigned_by_staff_id: uuid.UUID
    officer_name: str
    notes: str | None
    complaint: ComplaintRead
    inspection: InspectionRead | None = None


class PaginatedAssignments(BaseModel):
    items: list[AssignmentSummary]
    total: int
    page: int
    page_size: int
