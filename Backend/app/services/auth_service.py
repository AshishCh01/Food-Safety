import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.refresh_session import RefreshSession
from app.models.user import User
from app.repositories import refresh_session_repository, staff_repository, user_repository
from app.schemas.auth import AuthenticatedUser, LoginResponse, RegisterRequest, TokenResponse
from app.utils.enums import RefreshSessionRevokedReason, UserRole
from app.utils.exceptions import InactiveAccountError, InvalidCredentialsError, InvalidTokenError, UserAlreadyExistsError

logger = logging.getLogger(__name__)


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


def _as_aware(dt: datetime) -> datetime:
    """SQLite (the test database) drops tzinfo on DateTime(timezone=True)
    columns when reading a row back, even though it was written with a
    timezone-aware value; PostgreSQL does not have this issue. Normalizing
    on read keeps comparisons against `datetime.now(timezone.utc)` correct
    on both dialects."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _issue_refresh_session(db: Session, user_id: uuid.UUID, *, family_id: uuid.UUID) -> tuple[RefreshSession, str]:
    """Creates a new refresh_sessions row and returns it alongside the
    plaintext token - the plaintext exists only in this return value and the
    caller's response; only its hash is ever persisted."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    plaintext = generate_refresh_token()
    session = refresh_session_repository.create(
        db,
        user_id=user_id,
        family_id=family_id,
        token_hash=hash_refresh_token(plaintext),
        expires_at=now + timedelta(days=settings.refresh_token_expire_days),
    )
    return session, plaintext


def build_login_response(db: Session, user: User) -> LoginResponse:
    district_id = _district_id_for(db, user)
    session, refresh_token = _issue_refresh_session(db, user.id, family_id=uuid.uuid4())
    access_token = create_access_token(user.id, user.role.value, district_id, user.is_active, session_id=session.id)
    db.commit()
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


def _reject_replayed_session(db: Session, session: RefreshSession, *, now: datetime) -> None:
    """Called whenever a presented refresh token maps to a session that is
    already revoked - either it was already revoked when first looked up, or
    a concurrent request revoked it (rotated it) between this request's
    lookup and its own attempt to claim the rotation.

    Distinguishes two situations by how long ago the rotation happened:
    - Within `refresh_token_reuse_grace_seconds`: almost certainly a benign
      near-simultaneous concurrent refresh (e.g. two browser tabs sharing
      localStorage both waking up to refresh at once). Rejected, but no
      further action - the rotation that won is still valid.
    - Older than the grace window, and revoked specifically because it was
      *rotated* (not already logged-out/deactivated/reuse-flagged): this is
      replay of a stale, already-superseded refresh token - the strongest
      practical signal that the token was captured/leaked. The entire
      session family is revoked so the compromised lineage can't be used
      further, forcing full re-authentication.
    Any other revocation reason (logout, account_deactivated,
    reuse_detected) is already terminal - nothing more to do.
    """
    settings = get_settings()
    # `session` may already be sitting in this request's SQLAlchemy identity
    # map from the lookup earlier in refresh_access_token, in which case a
    # plain re-fetch (e.g. a fresh SELECT/`Session.get`) would return that
    # same cached Python object without picking up a concurrent request's
    # (different session's) commit - db.refresh() forces an actual read and
    # updates `session`'s attributes in place, so it always reflects the
    # current database state regardless of identity-map caching.
    db.refresh(session)
    if session.revoked_at is None:
        db.rollback()
        return

    if session.revoked_reason == RefreshSessionRevokedReason.ROTATED.value:
        age_seconds = (now - _as_aware(session.revoked_at)).total_seconds()
        if age_seconds > settings.refresh_token_reuse_grace_seconds:
            logger.warning(
                "Refresh token reuse detected for family %s (rotated %.1fs ago) - revoking session family.",
                session.family_id,
                age_seconds,
            )
            refresh_session_repository.revoke_family(
                db, session.family_id, reason=RefreshSessionRevokedReason.REUSE_DETECTED, now=now
            )
            db.commit()
            return

    db.rollback()


def refresh_access_token(db: Session, refresh_token: str) -> TokenResponse:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    token_hash = hash_refresh_token(refresh_token)

    session = refresh_session_repository.get_by_token_hash(db, token_hash)
    if session is None:
        raise InvalidTokenError()

    if session.revoked_at is not None:
        _reject_replayed_session(db, session, now=now)
        raise InvalidTokenError()

    if _as_aware(session.expires_at) <= now:
        db.rollback()
        raise InvalidTokenError("Refresh token has expired.")

    user = user_repository.get_by_id(db, session.user_id)
    if user is None:
        db.rollback()
        raise InvalidTokenError("User no longer exists.")
    if not user.is_active:
        refresh_session_repository.revoke(
            db, session, reason=RefreshSessionRevokedReason.ACCOUNT_DEACTIVATED, now=now
        )
        db.commit()
        raise InactiveAccountError()

    new_session_id = uuid.uuid4()
    won_rotation = refresh_session_repository.try_claim_for_rotation(
        db, session.id, replaced_by_id=new_session_id, now=now
    )
    if not won_rotation:
        # Another request rotated this exact token first, in the gap between
        # our lookup above and this claim attempt.
        _reject_replayed_session(db, session, now=now)
        raise InvalidTokenError()

    new_plaintext = generate_refresh_token()
    new_session = refresh_session_repository.create(
        db,
        user_id=user.id,
        family_id=session.family_id,
        token_hash=hash_refresh_token(new_plaintext),
        expires_at=now + timedelta(days=settings.refresh_token_expire_days),
        session_id=new_session_id,
    )

    district_id = _district_id_for(db, user)
    access_token = create_access_token(
        user.id, user.role.value, district_id, user.is_active, session_id=new_session.id
    )
    db.commit()
    return TokenResponse(access_token=access_token, refresh_token=new_plaintext)


def logout(db: Session, session_id: uuid.UUID | None) -> None:
    """Revokes the refresh session tied to the caller's current access token
    (see `sid` claim, app/core/security.py:create_access_token). A missing
    `session_id` (e.g. an access token issued before this feature existed)
    is tolerated silently - logout still succeeds client-side either way,
    since the access token itself expires shortly regardless."""
    if session_id is None:
        return
    session = refresh_session_repository.get_by_id(db, session_id)
    if session is None:
        return
    now = datetime.now(timezone.utc)
    refresh_session_repository.revoke(db, session, reason=RefreshSessionRevokedReason.LOGOUT, now=now)
    db.commit()


def revoke_all_sessions_for_user(db: Session, user_id: uuid.UUID) -> int:
    """Used when an account is deactivated (docs/SECURITY_AND_RBAC.md
    section 18) so existing refresh tokens stop working immediately rather
    than staying valid until they naturally expire. Returns the number of
    sessions revoked. Does not commit - callers already commit as part of
    the deactivation transaction."""
    now = datetime.now(timezone.utc)
    return refresh_session_repository.revoke_all_for_user(
        db, user_id, reason=RefreshSessionRevokedReason.ACCOUNT_DEACTIVATED, now=now
    )


# Rows deleted per transaction during cleanup - see
# refresh_session_repository.delete_expired_and_revoked_batch for why this
# is batched rather than one unbounded DELETE.
_CLEANUP_BATCH_SIZE = 1000


def count_sessions_eligible_for_cleanup(db: Session) -> int:
    """Read-only count for `scripts/cleanup_refresh_sessions.py --dry-run` -
    see docs/SECURITY_AND_RBAC.md section 20 for the retention policy."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    return refresh_session_repository.count_eligible_for_cleanup(
        db,
        now=now,
        retention_days=settings.refresh_session_retention_days,
        reuse_detected_retention_days=settings.refresh_session_reuse_detected_retention_days,
    )


def cleanup_expired_and_revoked_sessions(db: Session, *, batch_size: int = _CLEANUP_BATCH_SIZE) -> int:
    """Deletes refresh_sessions rows that are permanently unusable (expired,
    or revoked) and old enough to have aged past their retention window
    (docs/SECURITY_AND_RBAC.md section 20). Never touches a row that could
    still be presented successfully - only bookkeeping for already-dead
    sessions. Intended to be run periodically via
    scripts/cleanup_refresh_sessions.py (cron / Windows Task Scheduler /
    a scheduled CI job); there is no in-process scheduler and this project
    does not use Redis/Celery for background work.

    Commits after each batch so an individual transaction never holds a
    lock over the whole (potentially large) eligible set - important on a
    live database, e.g. the first run after a long gap without cleanup.
    Returns the total number of rows deleted.
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    total_deleted = 0
    while True:
        deleted = refresh_session_repository.delete_expired_and_revoked_batch(
            db,
            now=now,
            retention_days=settings.refresh_session_retention_days,
            reuse_detected_retention_days=settings.refresh_session_reuse_detected_retention_days,
            batch_size=batch_size,
        )
        db.commit()
        total_deleted += deleted
        if deleted < batch_size:
            break
    return total_deleted
