import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.district import District


def get_by_id(db: Session, district_id: uuid.UUID) -> District | None:
    return db.get(District, district_id)


def get_by_code(db: Session, code: str) -> District | None:
    return db.execute(select(District).where(District.code == code)).scalar_one_or_none()


def list_all(db: Session, *, is_active: bool | None = None) -> list[District]:
    stmt = select(District).options(joinedload(District.division))
    if is_active is not None:
        stmt = stmt.where(District.is_active == is_active)
    return list(db.execute(stmt.order_by(District.name)).scalars().all())
