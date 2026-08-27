import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inspection_finding import InspectionFinding
from app.utils.enums import FindingSeverity


def create(
    db: Session,
    *,
    inspection_id: uuid.UUID,
    check_code: str,
    finding: str,
    severity: FindingSeverity,
    compliant: bool,
    notes: str | None = None,
    corrective_action: str | None = None,
) -> InspectionFinding:
    record = InspectionFinding(
        inspection_id=inspection_id,
        check_code=check_code,
        finding=finding,
        severity=severity,
        compliant=compliant,
        notes=notes,
        corrective_action=corrective_action,
    )
    db.add(record)
    db.flush()
    return record


def list_by_inspection(db: Session, inspection_id: uuid.UUID) -> list[InspectionFinding]:
    stmt = (
        select(InspectionFinding)
        .where(InspectionFinding.inspection_id == inspection_id)
        .order_by(InspectionFinding.created_at)
    )
    return list(db.execute(stmt).scalars().all())
