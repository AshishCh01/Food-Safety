import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum

import bcrypt
import jwt

from app.core.config import get_settings
from app.utils.exceptions import InvalidTokenError


class TokenType(str, Enum):
    ACCESS = "access"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def _create_token(
    subject: uuid.UUID,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict | None = None,
) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload: dict = {
        "sub": str(subject),
        "type": token_type.value,
        "iat": now,
        "exp": now + expires_delta,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(
    user_id: uuid.UUID,
    role: str,
    district_id: uuid.UUID | None,
    is_active: bool,
    session_id: uuid.UUID | None = None,
) -> str:
    """`session_id` (claim `sid`) links this access token back to the
    refresh_sessions row it was issued alongside, so `POST /auth/logout` can
    revoke that specific server-side session using only the access token
    already required to call it - see app/services/auth_service.py and
    app/core/dependencies.get_current_access_token_claims. It is an internal
    JWT claim, never surfaced in an API response body."""
    settings = get_settings()
    return _create_token(
        user_id,
        TokenType.ACCESS,
        timedelta(minutes=settings.access_token_expire_minutes),
        extra_claims={
            "role": role,
            "district_id": str(district_id) if district_id else None,
            "status": "active" if is_active else "inactive",
            "sid": str(session_id) if session_id else None,
        },
    )


def decode_token(token: str, expected_type: TokenType) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise InvalidTokenError("Token has expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise InvalidTokenError("Invalid token.") from exc

    if payload.get("type") != expected_type.value:
        raise InvalidTokenError("Unexpected token type.")

    return payload


# --- Refresh tokens -----------------------------------------------------
# Refresh tokens are deliberately NOT JWTs. They are opaque, high-entropy
# random strings that only the database can resolve back to a user (via
# refresh_sessions.token_hash), which is what makes server-side revocation
# possible - a JWT refresh token would remain valid (its signature still
# verifies) for its whole lifetime no matter what the server does. Access
# tokens stay JWTs since they're short-lived and don't need to be
# individually revocable (docs/SECURITY_AND_RBAC.md section 18).


def generate_refresh_token() -> str:
    """~384 bits of entropy - infeasible to guess, so a plain SHA-256
    lookup hash (no HMAC secret needed) is sufficient, the same pattern used
    for API keys/session tokens generally."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
