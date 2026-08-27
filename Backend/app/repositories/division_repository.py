from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.division import Division


def list_all(db: Session) -> list[Division]:
    return list(db.execute(select(Division).order_by(Division.name)).scalars().all())


def get_by_code(db: Session, code: str) -> Division | None:
    return db.execute(select(Division).where(Division.code == code)).scalar_one_or_none()
