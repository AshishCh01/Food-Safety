import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.utils.enums import LabVerdict, SampleStatus


class SampleCreateRequest(BaseModel):
    item_description: str = Field(min_length=1, max_length=1000)
    quantity: str = Field(min_length=1, max_length=50)
    unit: str = Field(min_length=1, max_length=50)
    seal_number: str | None = Field(default=None, max_length=100)


class SampleDispatchRequest(BaseModel):
    food_analyst_id: uuid.UUID | None = None
    lab_name: str | None = Field(default=None, max_length=200)

    @model_validator(mode='after')
    def exactly_one_destination(self) -> 'SampleDispatchRequest':
        if self.food_analyst_id is None and not self.lab_name:
            raise ValueError('Either food_analyst_id or lab_name must be provided.')
        if self.food_analyst_id is not None and self.lab_name:
            raise ValueError('Provide either food_analyst_id or lab_name, not both.')
        return self


class LabTestResultRead(BaseModel):
    id: uuid.UUID
    sample_id: uuid.UUID
    food_analyst_id: uuid.UUID
    food_analyst_name: str
    tested_at: datetime
    report_storage_path: str | None
    verdict: LabVerdict
    remarks: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class SampleRead(BaseModel):
    id: uuid.UUID
    sample_code: str
    inspection_id: uuid.UUID
    item_description: str
    quantity: str
    unit: str
    seal_number: str | None
    collected_by_id: uuid.UUID
    collected_by_name: str
    collected_at: datetime
    status: SampleStatus
    dispatched_to_id: uuid.UUID | None
    dispatched_to_name: str | None
    dispatched_at: datetime | None
    lab_name: str | None
    lab_test_result: LabTestResultRead | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LabTestResultCreateRequest(BaseModel):
    verdict: LabVerdict
    remarks: str | None = Field(default=None, max_length=5000)


class PaginatedSamples(BaseModel):
    items: list[SampleRead]
    total: int
    page: int
    page_size: int