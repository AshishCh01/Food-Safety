import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.rag import RagCitation
from app.utils.enums import (
    AssistantMessageRole,
    ComplaintPriority,
    EvidenceAnalysisStatus,
    InvestigationStatus,
    TriageStatus,
)


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


class InvestigationRegulatoryGuidance(BaseModel):
    """One piece of model-drafted regulatory/procedural guidance, always
    paired with a citation resolved against an actually-retrieved RAG chunk
    (docs/RAG_ARCHITECTURE.md section 9) - an item whose citation could not
    be resolved is dropped before persistence, never shown uncited."""

    guidance: str
    citation: RagCitation


class InvestigationBriefRead(BaseModel):
    id: uuid.UUID
    complaint_id: uuid.UUID
    status: InvestigationStatus
    model_used: str

    case_summary: str | None
    # Deterministic, tool-fetched facts - never model-generated prose.
    relevant_evidence: list[dict[str, Any]]
    business_history: dict[str, Any] | None

    # Model-generated analytical layer.
    complaint_patterns: list[str]
    regulatory_guidance: list[InvestigationRegulatoryGuidance]
    risk_indicators: list[str]
    missing_information: list[str]
    suggested_actions: list[str]

    confidence: float | None
    is_uncertain: bool
    uncertainty_reasons: list[str]

    error_code: str | None
    error_message: str | None

    created_at: datetime


class AssistantApplicationDataUsage(BaseModel):
    """One piece of authorized application data the assistant pulled into its
    answer, e.g. {"tool": "A2", "label": "Previous complaints at this
    business", "summary": [...]}."""

    tool: str
    label: str
    summary: Any


class AssistantConversationCreateRequest(BaseModel):
    """`inspection_id` is optional: omit it for a general regulatory Q&A
    conversation with no case context. When provided, the caller must own
    that inspection - enforced server-side, never trusted from this payload
    alone (see app/api/inspector/router.py)."""

    inspection_id: uuid.UUID | None = None


class AssistantMessageCreateRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class AssistantMessageRead(BaseModel):
    id: uuid.UUID
    role: AssistantMessageRole
    content: str
    citations: list[RagCitation]
    application_data_used: list[AssistantApplicationDataUsage]
    is_uncertain: bool
    uncertainty_reason: str | None
    error_code: str | None
    error_message: str | None
    created_at: datetime


class AssistantConversationRead(BaseModel):
    id: uuid.UUID
    inspection_id: uuid.UUID | None
    complaint_id: uuid.UUID | None
    title: str | None
    messages: list[AssistantMessageRead]
    created_at: datetime
    updated_at: datetime


class AssistantConversationSummary(BaseModel):
    id: uuid.UUID
    inspection_id: uuid.UUID | None
    complaint_id: uuid.UUID | None
    title: str | None
    created_at: datetime
    updated_at: datetime


class PaginatedAssistantConversations(BaseModel):
    items: list[AssistantConversationSummary]
    total: int
    page: int
    page_size: int
