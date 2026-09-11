import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.utils.enums import UserRole

_DISTRICT_REQUIRED_ROLES = (UserRole.INSPECTOR, UserRole.DISTRICT_OFFICER)


class StaffCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    role: UserRole
    district_id: uuid.UUID | None = None
    employee_code: str = Field(min_length=1, max_length=50)
    designation: str | None = Field(default=None, max_length=100)

    @field_validator("role")
    @classmethod
    def role_must_be_staff(cls, value: UserRole) -> UserRole:
        if value not in (UserRole.INSPECTOR, UserRole.DISTRICT_OFFICER, UserRole.FOOD_ANALYST):
            raise ValueError("role must be 'inspector', 'district_officer', or 'food_analyst'")
        return value

    @model_validator(mode="after")
    def district_required_for_field_roles(self) -> "StaffCreateRequest":
        if self.role in _DISTRICT_REQUIRED_ROLES and self.district_id is None:
            raise ValueError("district_id is required for inspector and district_officer roles")
        return self


class StaffRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    email: str
    full_name: str
    phone: str | None
    role: UserRole
    district_id: uuid.UUID | None
    district_name: str | None
    employee_code: str
    designation: str | None
    is_active: bool
