import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.repositories import business_repository
from app.schemas.business import BusinessRead
from app.services import business_service
from app.utils.exceptions import BusinessNotFoundError

router = APIRouter(prefix="/businesses", tags=["businesses"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[BusinessRead])
def search_businesses(
    q: str | None = Query(default=None),
    district_id: uuid.UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[BusinessRead]:
    items, _total = business_service.search_businesses(
        db, q=q, district_id=district_id, page=page, page_size=page_size
    )
    return [business_service.to_business_read(item) for item in items]


@router.get("/{business_id}", response_model=BusinessRead)
def get_business(
    business_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> BusinessRead:
    business = business_repository.get_by_id(db, business_id)
    if business is None:
        raise BusinessNotFoundError()
    return business_service.to_business_read(business)
