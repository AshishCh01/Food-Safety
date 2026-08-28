import uuid
from datetime import date

from pydantic import BaseModel

from app.utils.enums import ComplaintPriority, ComplaintStatus


class StatusCount(BaseModel):
    status: ComplaintStatus
    count: int


class PriorityCount(BaseModel):
    priority: ComplaintPriority
    count: int


class CategoryCount(BaseModel):
    category_id: uuid.UUID
    category_name: str
    count: int


class TrendPoint(BaseModel):
    date: date
    count: int


class InspectorWorkload(BaseModel):
    inspector_staff_id: uuid.UUID
    inspector_name: str
    assigned_count: int
    in_progress_count: int
    completed_count: int
    total_count: int


class InspectionOutcomes(BaseModel):
    total_inspections: int
    scheduled: int
    in_progress: int
    completed: int
    compliant_findings: int
    non_compliant_findings: int


class DistrictAnalytics(BaseModel):
    district_id: uuid.UUID
    district_name: str
    total_complaints: int
    pending_complaints: int
    active_complaints: int
    resolved_complaints: int
    rejected_complaints: int
    status_breakdown: list[StatusCount]
    category_breakdown: list[CategoryCount]
    priority_breakdown: list[PriorityCount]
    complaint_trend: list[TrendPoint]
    average_resolution_hours: float | None
    inspector_workload: list[InspectorWorkload]
    inspection_outcomes: InspectionOutcomes


class DistrictSummary(BaseModel):
    district_id: uuid.UUID
    district_name: str
    division_name: str
    total_complaints: int
    pending_complaints: int
    active_complaints: int
    resolved_complaints: int


class StatewideAnalytics(BaseModel):
    total_districts: int
    total_complaints: int
    pending_complaints: int
    active_complaints: int
    resolved_complaints: int
    rejected_complaints: int
    status_breakdown: list[StatusCount]
    category_breakdown: list[CategoryCount]
    priority_breakdown: list[PriorityCount]
    complaint_trend: list[TrendPoint]
    average_resolution_hours: float | None
    district_breakdown: list[DistrictSummary]
