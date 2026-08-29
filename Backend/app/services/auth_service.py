import uuid

from sqlalchemy.orm import Session

from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories import staff_repository, user_repository
from app.schemas.auth import AuthenticatedUser, LoginResponse, RegisterRequest, TokenResponse
from app.utils.enums import UserRole
from app.utils.exceptions import InactiveAccountError, InvalidCredentialsError, InvalidTokenError, UserAlreadyExistsError


def register_citizen(db: Session, payload: RegisterRequest) -> User:
    if user_repository.get_by_email(db, payload.email):
        raise UserAlreadyExistsError()

    return user_repository.create(
        db,
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
        role=UserRole.CITIZEN,
    )


# A precomputed bcrypt hash of an unguessable placeholder, used only to give
# "unknown email" the same bcrypt-comparison cost as "known email, wrong
# password" - otherwise a nonexistent email short-circuits before
# verify_password runs, letting an attacker enumerate registered accounts by
# measuring response time.
_DUMMY_PASSWORD_HASH = hash_password("not-a-real-password-used-only-for-timing-parity")


def authenticate(db: Session, email: str, password: str) -> User:
    user = user_repository.get_by_email(db, email)
    password_hash = user.password_hash if user is not None else _DUMMY_PASSWORD_HASH
    password_matches = verify_password(password, password_hash)
    if user is None or not password_matches:
        raise InvalidCredentialsError()
    if not user.is_active:
        raise InactiveAccountError()

    user_repository.touch_last_login(db, user)
    return user


def _district_id_for(db: Session, user: User) -> uuid.UUID | None:
    if user.role not in (UserRole.INSPECTOR, UserRole.DISTRICT_OFFICER):
        return None
    profile = staff_repository.get_by_user_id(db, user.id)
    return profile.district_id if profile else None


def to_authenticated_user(db: Session, user: User) -> AuthenticatedUser:
    return AuthenticatedUser(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        district_id=_district_id_for(db, user),
        is_active=user.is_active,
    )


def build_login_response(db: Session, user: User) -> LoginResponse:
    district_id = _district_id_for(db, user)
    access_token = create_access_token(user.id, user.role.value, district_id, user.is_active)
    refresh_token = create_refresh_token(user.id)
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=AuthenticatedUser(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            district_id=district_id,
            is_active=user.is_active,
        ),
    )


def refresh_access_token(db: Session, refresh_token: str) -> TokenResponse:
    payload = decode_token(refresh_token, TokenType.REFRESH)
    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise InvalidTokenError() from exc

    user = user_repository.get_by_id(db, user_id)
    if user is None:
        raise InvalidTokenError("User no longer exists.")
    if not user.is_active:
        raise InactiveAccountError()

    district_id = _district_id_for(db, user)
    access_token = create_access_token(user.id, user.role.value, district_id, user.is_active)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)
