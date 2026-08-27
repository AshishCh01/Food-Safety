import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.assignment import Assignment
from app.utils.enums import AssignmentStatus

_EAGER_OPTIONS = (
    joinedload(Assignment.complaint),
    joinedload(Assignment.assigned_to),
    joinedload(Assignment.assigned_by),
)


def get_by_id(db: Session, assignment_id: uuid.UUID) -> Assignment | None:
    stmt = select(Assignment).where(Assignment.id == assignment_id).options(*_EAGER_OPTIONS)
    return db.execute(stmt).scalar_one_or_none()


def get_by_complaint_id(db: Session, complaint_id: uuid.UUID) -> Assignment | None:
    stmt = select(Assignment).where(Assignment.complaint_id == complaint_id).options(*_EAGER_OPTIONS)
    return db.execute(stmt).scalar_one_or_none()


def list_by_inspector(
    db: Session,
    inspector_staff_id: uuid.UUID,
    *,
    status: AssignmentStatus | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Assignment], int]:
    stmt = select(Assignment).where(Assignment.assigned_to_staff_id == inspector_staff_id)
    if status is not None:
        stmt = stmt.where(Assignment.status == status)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    stmt = (
        stmt.options(*_EAGER_OPTIONS)
        .order_by(Assignment.assigned_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(db.execute(stmt).scalars().all())
    return items, total


def create(
    db: Session,
    *,
    complaint_id: uuid.UUID,
    assigned_to_staff_id: uuid.UUID,
    assigned_by_staff_id: uuid.UUID,
    due_at: datetime | None = None,
    notes: str | None = None,
) -> Assignment:
    assignment = Assignment(
        complaint_id=complaint_id,
        assigned_to_staff_id=assigned_to_staff_id,
        assigned_by_staff_id=assigned_by_staff_id,
        due_at=due_at,
        notes=notes,
    )
    db.add(assignment)
    db.flush()
    return assignment
