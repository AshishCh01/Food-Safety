import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.repositories import district_repository, division_repository, user_repository
from app.schemas.district import DistrictRead
from app.schemas.staff import StaffCreateRequest, StaffRead
from app.schemas.user import PaginatedUsers, UserStatusUpdate, UserSummary
from app.services import district_service, staff_service
from app.utils.enums import UserRole
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)) -> dict:
    _, citizen_total = user_repository.list_users(db, role=UserRole.CITIZEN, page=1, page_size=1)
    _, officer_total = user_repository.list_users(db, role=UserRole.DISTRICT_OFFICER, page=1, page_size=1)
    _, inspector_total = user_repository.list_users(db, role=UserRole.INSPECTOR, page=1, page_size=1)
    _, admin_total = user_repository.list_users(db, role=UserRole.ADMIN, page=1, page_size=1)

    return {
        "division_count": len(division_repository.list_all(db)),
        "district_count": len(district_repository.list_all(db)),
        "citizen_count": citizen_total,
        "district_officer_count": officer_total,
        "inspector_count": inspector_total,
        "admin_count": admin_total,
    }


@router.get("/districts", response_model=list[DistrictRead])
def list_districts(
    is_active: bool | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[DistrictRead]:
    districts = district_service.list_districts(db, is_active=is_active)
    return [district_service.to_district_read(district) for district in districts]


@router.post("/staff", response_model=StaffRead, status_code=status.HTTP_201_CREATED)
def create_staff(payload: StaffCreateRequest, db: Session = Depends(get_db)) -> StaffRead:
    profile = staff_service.create_staff(db, payload)
    return staff_service.to_staff_read(profile)


@router.get("/users", response_model=PaginatedUsers)
def list_users(
    role: UserRole | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedUsers:
    items, total = user_repository.list_users(db, role=role, is_active=is_active, page=page, page_size=page_size)
    return PaginatedUsers(
        items=[UserSummary.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch("/users/{user_id}/status", response_model=UserSummary)
def update_user_status(
    user_id: uuid.UUID,
    payload: UserStatusUpdate,
    db: Session = Depends(get_db),
) -> UserSummary:
    user = user_repository.get_by_id(db, user_id)
    if user is None:
        raise NotFoundError("User was not found.")
    user = user_repository.set_active_status(db, user, payload.is_active)
    return UserSummary.model_validate(user)
