import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.complaint_category import ComplaintCategory


def get_by_id(db: Session, category_id: uuid.UUID) -> ComplaintCategory | None:
    return db.get(ComplaintCategory, category_id)


def get_by_key(db: Session, key: str) -> ComplaintCategory | None:
    return db.execute(select(ComplaintCategory).where(ComplaintCategory.key == key)).scalar_one_or_none()


def list_active(db: Session) -> list[ComplaintCategory]:
    stmt = select(ComplaintCategory).where(ComplaintCategory.is_active.is_(True)).order_by(ComplaintCategory.name)
    return list(db.execute(stmt).scalars().all())


def create(db: Session, *, key: str, name: str, description: str | None = None) -> ComplaintCategory:
    category = ComplaintCategory(key=key, name=name, description=description)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category
