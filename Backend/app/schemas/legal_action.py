import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.utils.enums import LegalActionStatus, LegalActionType


class LegalActionCreateRequest(BaseModel):
    lab_test_result_id: uuid.UUID | None = None
    fss_act_section: str | None = Field(default=None, max_length=100)
    action_type: LegalActionType
    fine_amount: Decimal | None = Field(default=None, ge=0)
    case_reference: str | None = Field(default=None, max_length=200)
    court_or_tribunal: str | None = Field(default=None, max_length=200)


class LegalActionUpdateRequest(BaseModel):
    status: LegalActionStatus | None = None
    outcome_notes: str | None = Field(default=None, max_length=5000)
    case_reference: str | None = Field(default=None, max_length=200)
    court_or_tribunal: str | None = Field(default=None, max_length=200)


class LegalActionRead(BaseModel):
    id: uuid.UUID
    complaint_id: uuid.UUID
    lab_test_result_id: uuid.UUID | None
    initiated_by_id: uuid.UUID
    initiated_by_name: str
    fss_act_section: str | None
    action_type: LegalActionType
    fine_amount: Decimal | None
    case_reference: str | None
    court_or_tribunal: str | None
    status: LegalActionStatus
    outcome_notes: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True