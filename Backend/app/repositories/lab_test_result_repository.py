import uuid

from sqlalchemy.orm import Session

from app.models.lab_test_result import LabTestResult


def create(db: Session, **kwargs) -> LabTestResult:
    result = LabTestResult(**kwargs)
    db.add(result)
    db.flush()
    return result


def get_by_sample_id(db: Session, sample_id: uuid.UUID) -> LabTestResult | None:
    from sqlalchemy import select
    return db.execute(select(LabTestResult).where(LabTestResult.sample_id == sample_id)).scalar_one_or_none()