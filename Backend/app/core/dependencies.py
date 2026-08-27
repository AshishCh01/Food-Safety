import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import TokenType, decode_token
from app.models.staff_profile import StaffProfile
from app.models.user import User
from app.repositories import staff_repository, user_repository
from app.utils.enums import UserRole
from app.utils.exceptions import (
    AuthenticationRequiredError,
    InactiveAccountError,
    InvalidTokenError,
    PermissionDeniedError,
)

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise AuthenticationRequiredError()

    payload = decode_token(credentials.credentials, TokenType.ACCESS)

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise InvalidTokenError() from exc

    user = user_repository.get_by_id(db, user_id)
    if user is None:
        raise InvalidTokenError("User no longer exists.")
    if not user.is_active:
        raise InactiveAccountError()

    return user


def require_roles(*roles: UserRole):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise PermissionDeniedError()
        return current_user

    return dependency


require_admin = require_roles(UserRole.ADMIN)
require_district_officer = require_roles(UserRole.DISTRICT_OFFICER)
require_inspector = require_roles(UserRole.INSPECTOR)
require_citizen = require_roles(UserRole.CITIZEN)
require_staff = require_roles(UserRole.DISTRICT_OFFICER, UserRole.INSPECTOR)


def get_current_staff_profile(
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
) -> StaffProfile:
    """Resolves the district-scoped staff profile for the current user.

    Downstream handlers must derive district scope only from this profile,
    never from client-supplied query parameters, to enforce district
    isolation server-side.
    """
    profile = staff_repository.get_by_user_id(db, current_user.id)
    if profile is None or not profile.is_active:
        raise PermissionDeniedError("Staff profile is not active.")
    return profile
