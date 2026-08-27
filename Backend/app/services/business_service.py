import uuid

from sqlalchemy.orm import Session

from app.models.business import Business
from app.repositories import business_repository
from app.schemas.business import BusinessInput, BusinessRead
from app.utils.geo import validate_coordinates


def get_or_create_business(
    db: Session,
    *,
    district_id: uuid.UUID,
    created_by_user_id: uuid.UUID,
    payload: BusinessInput,
) -> Business:
    validate_coordinates(payload.latitude, payload.longitude)

    existing = business_repository.find_match(
        db, district_id=district_id, business_name=payload.business_name, address=payload.address
    )
    if existing is not None:
        return existing

    return business_repository.create(
        db,
        business_name=payload.business_name,
        business_type=payload.business_type,
        license_number=payload.license_number,
        address=payload.address,
        district_id=district_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        contact_phone=payload.contact_phone,
        created_by_user_id=created_by_user_id,
    )


def search_businesses(
    db: Session, *, q: str | None, district_id: uuid.UUID | None, page: int, page_size: int
) -> tuple[list[Business], int]:
    return business_repository.search(db, q=q, district_id=district_id, page=page, page_size=page_size)


def to_business_read(business: Business) -> BusinessRead:
    return BusinessRead(
        id=business.id,
        business_name=business.business_name,
        business_type=business.business_type,
        license_number=business.license_number,
        address=business.address,
        district_id=business.district_id,
        latitude=float(business.latitude) if business.latitude is not None else None,
        longitude=float(business.longitude) if business.longitude is not None else None,
        contact_phone=business.contact_phone,
        is_active=business.is_active,
    )
