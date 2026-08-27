from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.complaint_category import ComplaintCategoryRead
from app.schemas.district import DistrictRead
from app.services import complaint_category_service, district_service, geocoding_service
from app.utils.geo import validate_coordinates

router = APIRouter(tags=["reference"], dependencies=[Depends(get_current_user)])


@router.get("/districts", response_model=list[DistrictRead])
def list_districts(
    is_active: bool | None = Query(default=True),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[DistrictRead]:
    districts = district_service.list_districts(db, is_active=is_active)
    return [district_service.to_district_read(district) for district in districts]


@router.get("/complaint-categories", response_model=list[ComplaintCategoryRead])
def list_complaint_categories(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ComplaintCategoryRead]:
    categories = complaint_category_service.list_categories(db)
    return [complaint_category_service.to_category_read(category) for category in categories]


@router.get("/reverse-geocode")
def reverse_geocode(
    lat: float = Query(...),
    lon: float = Query(...),
    _: User = Depends(get_current_user),
) -> dict:
    validate_coordinates(lat, lon)
    address = geocoding_service.reverse_geocode(lat, lon)
    return {"address": address}
