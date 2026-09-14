import uuid
from datetime import datetime

from sqlalchemy import func, select, or_, case
from sqlalchemy.orm import Session, joinedload

from app.models.assignment import Assignment
from app.models.complaint import Complaint
from app.utils.enums import AssignmentStatus

_EAGER_OPTIONS = (
    joinedload(Assignment.complaint).joinedload(Complaint.business),
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
    sort: str = "due_at",
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Assignment], int]:
    stmt = select(Assignment).join(Assignment.complaint).where(Assignment.assigned_to_staff_id == inspector_staff_id)
    if status is not None:
        stmt = stmt.where(Assignment.status == status)
    
    if q:
        stmt = stmt.where(
            or_(
                Complaint.complaint_number.ilike(f"%{q}%"),
                Complaint.title.ilike(f"%{q}%")
            )
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    if sort == "priority":
        priority_order = case(
            (Complaint.priority == 'critical', 4),
            (Complaint.priority == 'high', 3),
            (Complaint.priority == 'medium', 2),
            (Complaint.priority == 'low', 1),
            else_=0
        )
        stmt = stmt.order_by(priority_order.desc(), Assignment.due_at.asc().nullslast())
    elif sort == "assigned_at":
        stmt = stmt.order_by(Assignment.assigned_at.desc())
    else:  # due_at
        stmt = stmt.order_by(Assignment.due_at.asc().nullslast())

    stmt = (
        stmt.options(*_EAGER_OPTIONS)
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
