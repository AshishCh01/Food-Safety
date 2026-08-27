import uuid

from pydantic import BaseModel, EmailStr, Field

from app.utils.enums import UserRole


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=20)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthenticatedUser(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    district_id: uuid.UUID | None = None
    is_active: bool


class LoginResponse(TokenResponse):
    user: AuthenticatedUser
