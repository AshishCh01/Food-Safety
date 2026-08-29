import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evidence_analysis import EvidenceAnalysis


def create(db: Session, analysis: EvidenceAnalysis) -> EvidenceAnalysis:
    db.add(analysis)
    db.flush()
    return analysis


def get_latest_by_evidence(db: Session, evidence_id: uuid.UUID) -> EvidenceAnalysis | None:
    stmt = (
        select(EvidenceAnalysis)
        .where(EvidenceAnalysis.evidence_id == evidence_id)
        .order_by(EvidenceAnalysis.created_at.desc())
        .limit(1)
    )
    return db.execute(stmt).scalars().first()


def get_latest_by_evidence_ids(db: Session, evidence_ids: list[uuid.UUID]) -> dict[uuid.UUID, EvidenceAnalysis]:
    """Batch equivalent of get_latest_by_evidence for a list of evidence
    items - one query instead of one-per-item (see
    app/agents/inspector_assistant/tools.py and
    app/agents/investigation/tools.py, both of which summarize every
    evidence item on a case)."""
    if not evidence_ids:
        return {}

    stmt = (
        select(EvidenceAnalysis)
        .where(EvidenceAnalysis.evidence_id.in_(evidence_ids))
        .order_by(EvidenceAnalysis.evidence_id, EvidenceAnalysis.created_at.desc())
    )
    latest: dict[uuid.UUID, EvidenceAnalysis] = {}
    for analysis in db.execute(stmt).scalars().all():
        # Rows arrive grouped by evidence_id (created_at desc within each
        # group), so the first row seen per evidence_id is the latest one.
        latest.setdefault(analysis.evidence_id, analysis)
    return latest


def list_by_evidence(db: Session, evidence_id: uuid.UUID) -> list[EvidenceAnalysis]:
    stmt = (
        select(EvidenceAnalysis)
        .where(EvidenceAnalysis.evidence_id == evidence_id)
        .order_by(EvidenceAnalysis.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())
