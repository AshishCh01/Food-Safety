"""Controlled tools for the Inspector Assistant
(docs/AI_AGENTS_ARCHITECTURE.md sections 9-10, docs/SECURITY_AND_RBAC.md
section 9). Every tool here takes an already-scoped ORM object or the
authenticated `staff` profile - never a raw ID chosen by the model - so
authorization is enforced by which Python objects the caller passes in, not
by anything the LLM outputs. See `app/agents/inspector_assistant/agent.py`
for how these are invoked: entity IDs always come from the conversation's own
server-resolved inspection/complaint/business context, which was itself
resolved via `inspection_service.get_inspection_for_inspector` when the
conversation was created.
"""

import uuid

from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.complaint import Complaint
from app.models.inspection import Inspection
from app.models.staff_profile import StaffProfile
from app.rag import retrieval
from app.repositories import complaint_repository, evidence_analysis_repository, evidence_repository, inspection_repository
from app.utils.enums import INSPECTION_GUIDELINE_DOCUMENT_TYPES, REGULATION_DOCUMENT_TYPES, EvidenceAnalysisStatus


def search_regulations(
    db: Session, query: str, *, business_type: str | None = None
) -> list[retrieval.RetrievedChunk]:
    return retrieval.search(db, query, document_types=list(REGULATION_DOCUMENT_TYPES), business_type=business_type)


def search_inspection_guidelines(
    db: Session, query: str, *, business_type: str | None = None
) -> list[retrieval.RetrievedChunk]:
    return retrieval.search(
        db, query, document_types=list(INSPECTION_GUIDELINE_DOCUMENT_TYPES), business_type=business_type
    )


def get_complaint(complaint: Complaint) -> dict:
    return {
        "complaint_number": complaint.complaint_number,
        "title": complaint.title,
        "description": complaint.description,
        "category": complaint.category.name if complaint.category else None,
        "status": complaint.status.value,
        "priority": complaint.priority.value if complaint.priority else None,
        "reported_at": complaint.reported_at.isoformat() if complaint.reported_at else None,
    }


def get_business(business: Business) -> dict:
    return {
        "business_name": business.business_name,
        "business_type": business.business_type,
        "license_number": business.license_number,
        "address": business.address,
    }


def get_previous_complaints(
    db: Session, business: Business, staff: StaffProfile, *, exclude_complaint_id: uuid.UUID | None = None
) -> list[dict]:
    """District-scoped to the requesting inspector's own district - see
    complaint_repository.list_by_business."""
    complaints = complaint_repository.list_by_business(
        db, business.id, staff.district_id, exclude_complaint_id=exclude_complaint_id
    )
    return [
        {
            "complaint_number": complaint.complaint_number,
            "title": complaint.title,
            "category": complaint.category.name if complaint.category else None,
            "status": complaint.status.value,
            "created_at": complaint.created_at.isoformat(),
        }
        for complaint in complaints
    ]


def get_inspection_history(
    db: Session, business: Business, staff: StaffProfile, *, exclude_inspection_id: uuid.UUID | None = None
) -> list[dict]:
    """District-scoped to the requesting inspector's own district - see
    inspection_repository.list_by_business."""
    inspections = inspection_repository.list_by_business(
        db, business.id, staff.district_id, exclude_inspection_id=exclude_inspection_id
    )
    return [
        {
            "complaint_number": inspection.complaint.complaint_number,
            "inspection_status": inspection.inspection_status.value,
            "summary": inspection.summary,
            "action_recommended": inspection.action_recommended,
            "completed_at": inspection.completed_at.isoformat() if inspection.completed_at else None,
        }
        for inspection in inspections
    ]


def get_evidence_analysis(db: Session, inspection: Inspection) -> list[dict]:
    """Latest completed AI evidence analysis for every evidence item on
    `inspection`. `inspection` must already be scoped to the requesting
    inspector by the caller (see inspection_service.get_inspection_for_inspector)."""
    items = evidence_repository.list_by_inspection(db, inspection.id)
    latest_by_evidence_id = evidence_analysis_repository.get_latest_by_evidence_ids(db, [item.id for item in items])
    summaries = []
    for item in items:
        analysis = latest_by_evidence_id.get(item.id)
        if analysis is None or analysis.status != EvidenceAnalysisStatus.COMPLETED:
            continue
        summaries.append(
            {
                "file_name": item.file_name,
                "product_name": analysis.product_name,
                "expiry_date_text": analysis.expiry_date_text,
                "possible_expired": analysis.possible_expired,
                "packaging_observations": analysis.packaging_observations,
                "hygiene_observations": analysis.hygiene_observations,
                "foreign_object_observations": analysis.foreign_object_observations,
                "is_uncertain": analysis.is_uncertain,
            }
        )
    return summaries
