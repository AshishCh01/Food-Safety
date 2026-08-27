import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.inspection import Inspection
from app.utils.enums import InspectionStatus

_EAGER_OPTIONS = (
    joinedload(Inspection.complaint),
    joinedload(Inspection.inspector),
    joinedload(Inspection.findings),
)


def get_by_id(db: Session, inspection_id: uuid.UUID) -> Inspection | None:
    stmt = select(Inspection).where(Inspection.id == inspection_id).options(*_EAGER_OPTIONS)
    return db.execute(stmt).unique().scalar_one_or_none()


def get_by_complaint_id(db: Session, complaint_id: uuid.UUID) -> Inspection | None:
    stmt = select(Inspection).where(Inspection.complaint_id == complaint_id).options(*_EAGER_OPTIONS)
    return db.execute(stmt).unique().scalar_one_or_none()


def list_by_inspector(
    db: Session,
    inspector_staff_id: uuid.UUID,
    *,
    status: InspectionStatus | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Inspection], int]:
    stmt = select(Inspection).where(Inspection.inspector_id == inspector_staff_id)
    if status is not None:
        stmt = stmt.where(Inspection.inspection_status == status)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    stmt = (
        stmt.options(*_EAGER_OPTIONS)
        .order_by(Inspection.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(db.execute(stmt).unique().scalars().all())
    return items, total


def create(db: Session, inspection: Inspection) -> Inspection:
    db.add(inspection)
    db.flush()
    return inspection
