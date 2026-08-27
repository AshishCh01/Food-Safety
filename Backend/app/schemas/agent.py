import uuid
from datetime import datetime

from pydantic import BaseModel

from app.utils.enums import ComplaintPriority, EvidenceAnalysisStatus, TriageStatus


class ComplaintTriageEntities(BaseModel):
    """Business/product information extracted from the complaint text.

    Fields are only populated when explicitly present in the citizen's
    description - the agent is instructed not to invent them.
    """

    business_name: str | None = None
    product: str | None = None


class ComplaintTriageRead(BaseModel):
    id: uuid.UUID
    complaint_id: uuid.UUID
    status: TriageStatus
    model_used: str

    suggested_category_id: uuid.UUID | None
    suggested_category_name: str | None
    suggested_category_raw: str | None
    category_match_uncertain: bool

    suggested_priority: ComplaintPriority | None
    summary: str | None
    entities: ComplaintTriageEntities
    missing_information: list[str]
    confidence: float | None
    is_uncertain: bool

    error_code: str | None
    error_message: str | None

    created_at: datetime


class EvidenceAnalysisRead(BaseModel):
    id: uuid.UUID
    evidence_id: uuid.UUID
    status: EvidenceAnalysisStatus
    model_used: str

    extracted_text: str | None
    product_name: str | None
    manufacturer: str | None
    batch_lot_number: str | None
    manufacturing_date_text: str | None
    expiry_date_text: str | None
    possible_expired: bool | None

    packaging_observations: str | None
    hygiene_observations: str | None
    foreign_object_observations: str | None

    uncertainty_notes: list[str]
    confidence: float | None
    is_uncertain: bool

    error_code: str | None
    error_message: str | None

    created_at: datetime
