import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.sample import Sample
from app.utils.enums import SampleStatus


def create(db: Session, **kwargs) -> Sample:
    sample = Sample(**kwargs)
    db.add(sample)
    db.flush()
    return sample


def get_by_id(db: Session, sample_id: uuid.UUID) -> Sample | None:
    return db.get(Sample, sample_id)


def list_by_inspection(db: Session, inspection_id: uuid.UUID) -> list[Sample]:
    return list(
        db.execute(select(Sample).where(Sample.inspection_id == inspection_id).order_by(Sample.created_at)).scalars()
    )


def count_by_inspection(db: Session, inspection_id: uuid.UUID) -> int:
    return db.execute(
        select(func.count()).select_from(Sample).where(Sample.inspection_id == inspection_id)
    ).scalar_one()


def list_for_analyst(
    db: Session,
    analyst_staff_id: uuid.UUID,
    *,
    status: SampleStatus | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Sample], int]:
    q = select(Sample).where(Sample.dispatched_to_id == analyst_staff_id)
    if status is not None:
        q = q.where(Sample.status == status)
    total = db.execute(select(func.count()).select_from(q.subquery())).scalar_one()
    items = list(
        db.execute(q.order_by(Sample.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).scalars()
    )
    return items, total