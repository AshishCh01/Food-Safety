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


def list_by_evidence(db: Session, evidence_id: uuid.UUID) -> list[EvidenceAnalysis]:
    stmt = (
        select(EvidenceAnalysis)
        .where(EvidenceAnalysis.evidence_id == evidence_id)
        .order_by(EvidenceAnalysis.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())
