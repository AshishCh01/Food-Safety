import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.utils.enums import UserRole


class StaffCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    role: UserRole
    district_id: uuid.UUID
    employee_code: str = Field(min_length=1, max_length=50)
    designation: str | None = Field(default=None, max_length=100)

    @field_validator("role")
    @classmethod
    def role_must_be_staff(cls, value: UserRole) -> UserRole:
        if value not in (UserRole.INSPECTOR, UserRole.DISTRICT_OFFICER):
            raise ValueError("role must be 'inspector' or 'district_officer'")
        return value


class StaffRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    email: str
    full_name: str
    phone: str | None
    role: UserRole
    district_id: uuid.UUID
    district_name: str
    employee_code: str
    designation: str | None
    is_active: bool
