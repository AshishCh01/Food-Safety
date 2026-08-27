import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.business import Business


def get_by_id(db: Session, business_id: uuid.UUID) -> Business | None:
    return db.get(Business, business_id)


def find_match(db: Session, *, district_id: uuid.UUID, business_name: str, address: str) -> Business | None:
    stmt = select(Business).where(
        Business.district_id == district_id,
        func.lower(Business.business_name) == business_name.strip().lower(),
        func.lower(Business.address) == address.strip().lower(),
    )
    return db.execute(stmt).scalar_one_or_none()


def search(
    db: Session,
    *,
    q: str | None = None,
    district_id: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Business], int]:
    stmt = select(Business).where(Business.is_active.is_(True))
    if district_id is not None:
        stmt = stmt.where(Business.district_id == district_id)
    if q:
        stmt = stmt.where(func.lower(Business.business_name).contains(q.strip().lower()))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    stmt = stmt.order_by(Business.business_name).offset((page - 1) * page_size).limit(page_size)
    items = list(db.execute(stmt).scalars().all())
    return items, total


def create(
    db: Session,
    *,
    business_name: str,
    business_type: str | None,
    license_number: str | None,
    address: str,
    district_id: uuid.UUID,
    latitude: float | None,
    longitude: float | None,
    contact_phone: str | None,
    created_by_user_id: uuid.UUID | None,
) -> Business:
    business = Business(
        business_name=business_name,
        business_type=business_type,
        license_number=license_number,
        address=address,
        district_id=district_id,
        latitude=latitude,
        longitude=longitude,
        contact_phone=contact_phone,
        created_by_user_id=created_by_user_id,
    )
    db.add(business)
    db.commit()
    db.refresh(business)
    return business
