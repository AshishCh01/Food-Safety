"""Controlled tools for the Investigation Agent
(docs/AI_AGENTS_ARCHITECTURE.md section 6, docs/SECURITY_AND_RBAC.md section
9). Every tool here takes an already-scoped ORM object or the authenticated
`staff` profile - never a raw ID chosen by the model - so authorization is
enforced by which Python objects the caller passes in, not by anything the
LLM outputs. See `app/agents/investigation/agent.py`: `complaint` is always
resolved via `complaint_service.get_complaint_for_officer` before any of
these tools run, and every cross-business lookup here is additionally scoped
to `staff.district_id`, so a district officer can never pull another
district's history through this agent.

Every function returns plain dicts/lists - never ORM objects - so the agent
module can embed the result directly into a prompt or the persisted brief
without leaking unrelated columns.
"""

import uuid

from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.complaint import Complaint
from app.models.inspection import Inspection
from app.models.staff_profile import StaffProfile
from app.rag import retrieval
from app.repositories import (
    complaint_repository,
    complaint_triage_repository,
    evidence_analysis_repository,
    evidence_repository,
    inspection_repository,
)
from app.utils.enums import EvidenceAnalysisStatus, TriageStatus


def get_complaint(complaint: Complaint) -> dict:
    return {
        "complaint_number": complaint.complaint_number,
        "title": complaint.title,
        "description": complaint.description,
        "category": complaint.category.name if complaint.category else None,
        "status": complaint.status.value,
        "priority": complaint.priority.value if complaint.priority else None,
        "address_line": complaint.address_line,
        "reported_at": complaint.reported_at.isoformat() if complaint.reported_at else None,
        "verified_at": complaint.verified_at.isoformat() if complaint.verified_at else None,
    }


def get_complaint_triage(db: Session, complaint: Complaint) -> dict | None:
    """Latest completed AI triage suggestion for this complaint, if any -
    advisory only, never the authoritative category/priority."""
    triage = complaint_triage_repository.get_latest_by_complaint(db, complaint.id)
    if triage is None or triage.status != TriageStatus.COMPLETED:
        return None
    return {
        "suggested_category": triage.suggested_category.name if triage.suggested_category else triage.suggested_category_raw,
        "category_match_uncertain": triage.category_match_uncertain,
        "suggested_priority": triage.suggested_priority.value if triage.suggested_priority else None,
        "summary": triage.summary,
        "entities": triage.entities or {},
        "missing_information": triage.missing_information or [],
        "is_uncertain": triage.is_uncertain,
    }


def get_business(business: Business) -> dict:
    return {
        "business_name": business.business_name,
        "business_type": business.business_type,
        "license_number": business.license_number,
        "address": business.address,
        "is_active": business.is_active,
    }


def get_complaint_history(
    db: Session, business: Business, staff: StaffProfile, *, exclude_complaint_id: uuid.UUID | None = None
) -> list[dict]:
    """Other complaints against the same business, scoped to the requesting
    officer's own district - see complaint_repository.list_by_business."""
    complaints = complaint_repository.list_by_business(
        db, business.id, staff.district_id, exclude_complaint_id=exclude_complaint_id
    )
    return [
        {
            "complaint_number": complaint.complaint_number,
            "title": complaint.title,
            "category": complaint.category.name if complaint.category else None,
            "status": complaint.status.value,
            "priority": complaint.priority.value if complaint.priority else None,
            "created_at": complaint.created_at.isoformat(),
        }
        for complaint in complaints
    ]


def get_inspection_history(
    db: Session, business: Business, staff: StaffProfile, *, exclude_inspection_id: uuid.UUID | None = None
) -> list[dict]:
    """Prior inspections against the same business, scoped to the requesting
    officer's own district - see inspection_repository.list_by_business."""
    inspections = inspection_repository.list_by_business(
        db, business.id, staff.district_id, exclude_inspection_id=exclude_inspection_id
    )
    return [
        {
            "complaint_number": inspection.complaint.complaint_number,
            "inspection_status": inspection.inspection_status.value,
            "summary": inspection.summary,
            "action_recommended": inspection.action_recommended,
            "findings": [
                {
                    "check_code": finding.check_code,
                    "finding": finding.finding,
                    "severity": finding.severity.value,
                    "compliant": finding.compliant,
                }
                for finding in inspection.findings
            ],
            "completed_at": inspection.completed_at.isoformat() if inspection.completed_at else None,
        }
        for inspection in inspections
    ]


def get_current_inspection(inspection: Inspection | None) -> dict | None:
    """`inspection` must already be scoped to the officer's district by the
    caller (it is looked up via the already-scoped `complaint`)."""
    if inspection is None:
        return None
    return {
        "inspection_status": inspection.inspection_status.value,
        "scheduled_at": inspection.scheduled_at.isoformat() if inspection.scheduled_at else None,
        "started_at": inspection.started_at.isoformat() if inspection.started_at else None,
        "completed_at": inspection.completed_at.isoformat() if inspection.completed_at else None,
        "summary": inspection.summary,
        "action_recommended": inspection.action_recommended,
        "findings": [
            {
                "check_code": finding.check_code,
                "finding": finding.finding,
                "severity": finding.severity.value,
                "compliant": finding.compliant,
                "notes": finding.notes,
                "corrective_action": finding.corrective_action,
            }
            for finding in inspection.findings
        ],
    }


def get_evidence_analysis(db: Session, complaint: Complaint) -> list[dict]:
    """Latest completed AI evidence analysis for every evidence item on
    `complaint`. `complaint` must already be scoped to the requesting officer
    by the caller (see complaint_service.get_complaint_for_officer)."""
    items = evidence_repository.list_by_complaint(db, complaint.id)
    summaries = []
    for item in items:
        analysis = evidence_analysis_repository.get_latest_by_evidence(db, item.id)
        if analysis is None or analysis.status != EvidenceAnalysisStatus.COMPLETED:
            continue
        summaries.append(
            {
                "evidence_id": str(item.id),
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


def search_regulations(
    db: Session, query: str, *, business_type: str | None = None, top_k: int | None = None
) -> list[retrieval.RetrievedChunk]:
    """Searches the full RAG knowledge base (no document-type restriction) so
    the investigation brief can cite laws, regulations, licensing, and
    inspection/hygiene guidance alike."""
    return retrieval.search(db, query, top_k=top_k, business_type=business_type)
