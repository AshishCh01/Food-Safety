from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.staff_profile import StaffProfile
from app.repositories import district_repository, staff_repository, user_repository
from app.schemas.staff import StaffCreateRequest, StaffRead
from app.utils.enums import UserRole
from app.utils.exceptions import ConflictError, NotFoundError, UserAlreadyExistsError


def create_staff(db: Session, payload: StaffCreateRequest) -> StaffProfile:
    district = district_repository.get_by_id(db, payload.district_id)
    if district is None:
        raise NotFoundError("District was not found.")

    if user_repository.get_by_email(db, payload.email):
        raise UserAlreadyExistsError()

    if staff_repository.get_by_employee_code(db, payload.employee_code):
        raise ConflictError("A staff member with this employee code already exists.")

    if payload.role == UserRole.DISTRICT_OFFICER:
        existing_officer = staff_repository.get_active_officer_for_district(db, payload.district_id)
        if existing_officer is not None:
            raise ConflictError("This district already has an active district officer.")

    user = user_repository.create(
        db,
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
        role=payload.role,
    )

    return staff_repository.create(
        db,
        user_id=user.id,
        district_id=payload.district_id,
        role=payload.role,
        employee_code=payload.employee_code,
        designation=payload.designation,
    )


def to_staff_read(profile: StaffProfile) -> StaffRead:
    return StaffRead(
        id=profile.id,
        user_id=profile.user_id,
        email=profile.user.email,
        full_name=profile.user.full_name,
        phone=profile.user.phone,
        role=profile.role,
        district_id=profile.district_id,
        district_name=profile.district.name,
        employee_code=profile.employee_code,
        designation=profile.designation,
        is_active=profile.is_active,
    )
