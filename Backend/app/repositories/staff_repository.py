import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.staff_profile import StaffProfile
from app.utils.enums import UserRole


def get_by_id(db: Session, staff_id: uuid.UUID) -> StaffProfile | None:
    stmt = (
        select(StaffProfile)
        .options(joinedload(StaffProfile.user), joinedload(StaffProfile.district))
        .where(StaffProfile.id == staff_id)
    )
    return db.execute(stmt).scalar_one_or_none()


def get_by_user_id(db: Session, user_id: uuid.UUID) -> StaffProfile | None:
    stmt = select(StaffProfile).where(StaffProfile.user_id == user_id)
    return db.execute(stmt).scalar_one_or_none()


def get_by_employee_code(db: Session, employee_code: str) -> StaffProfile | None:
    stmt = select(StaffProfile).where(StaffProfile.employee_code == employee_code)
    return db.execute(stmt).scalar_one_or_none()


def get_active_officer_for_district(db: Session, district_id: uuid.UUID) -> StaffProfile | None:
    stmt = select(StaffProfile).where(
        StaffProfile.district_id == district_id,
        StaffProfile.role == UserRole.DISTRICT_OFFICER,
        StaffProfile.is_active.is_(True),
    )
    return db.execute(stmt).scalar_one_or_none()


def list_by_district(
    db: Session,
    district_id: uuid.UUID,
    *,
    role: UserRole | None = None,
    is_active: bool | None = True,
) -> list[StaffProfile]:
    stmt = (
        select(StaffProfile)
        .options(joinedload(StaffProfile.user), joinedload(StaffProfile.district))
        .where(StaffProfile.district_id == district_id)
    )
    if role is not None:
        stmt = stmt.where(StaffProfile.role == role)
    if is_active is not None:
        stmt = stmt.where(StaffProfile.is_active == is_active)
    return list(db.execute(stmt).scalars().all())


def count_by_district_role(db: Session, district_id: uuid.UUID, role: UserRole) -> int:
    stmt = select(func.count()).select_from(StaffProfile).where(
        StaffProfile.district_id == district_id,
        StaffProfile.role == role,
        StaffProfile.is_active.is_(True),
    )
    return db.execute(stmt).scalar_one()


def create(
    db: Session,
    *,
    user_id: uuid.UUID,
    district_id: uuid.UUID,
    role: UserRole,
    employee_code: str,
    designation: str | None,
) -> StaffProfile:
    profile = StaffProfile(
        user_id=user_id,
        district_id=district_id,
        role=role,
        employee_code=employee_code,
        designation=designation,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
