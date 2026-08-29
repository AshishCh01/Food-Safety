import uuid
from datetime import datetime, timedelta

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.orm import Session

from app.models.refresh_session import RefreshSession
from app.utils.enums import RefreshSessionRevokedReason


def create(
    db: Session,
    *,
    user_id: uuid.UUID,
    family_id: uuid.UUID,
    token_hash: str,
    expires_at: datetime,
    session_id: uuid.UUID | None = None,
) -> RefreshSession:
    """`session_id` lets a caller pre-generate the id (e.g. rotation needs to
    know the new session's id before creating it, to record it as the old
    session's `replaced_by_id` in the same atomic claim - see
    app/services/auth_service.py:refresh_access_token). Defaults to a fresh
    UUID when the caller doesn't need to reference it up front (e.g. login)."""
    session = RefreshSession(
        id=session_id or uuid.uuid4(),
        user_id=user_id,
        family_id=family_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(session)
    db.flush()
    return session


def get_by_token_hash(db: Session, token_hash: str) -> RefreshSession | None:
    stmt = select(RefreshSession).where(RefreshSession.token_hash == token_hash)
    return db.execute(stmt).scalar_one_or_none()


def get_by_id(db: Session, session_id: uuid.UUID) -> RefreshSession | None:
    return db.get(RefreshSession, session_id)


def try_claim_for_rotation(db: Session, session_id: uuid.UUID, *, replaced_by_id: uuid.UUID, now: datetime) -> bool:
    """Atomically revokes `session_id` for rotation, but only if it is still
    unrevoked at the moment the UPDATE executes. Returns True iff this call
    won the race and performed the revoke.

    This is the concurrency-safety mechanism for simultaneous refresh
    requests presenting the same token: the database's row-level
    consistency for a single UPDATE statement guarantees only one caller can
    ever see rowcount == 1 for a given `session_id`, no matter how many
    processes/requests race to rotate it at once. See
    app/services/auth_service.py:refresh_access_token for how the loser is
    handled (rejected, and only escalated to a family-wide revocation if the
    winning rotation happened outside the benign-concurrency grace window).
    """
    stmt = (
        update(RefreshSession)
        .where(RefreshSession.id == session_id, RefreshSession.revoked_at.is_(None))
        .values(
            revoked_at=now,
            revoked_reason=RefreshSessionRevokedReason.ROTATED.value,
            replaced_by_id=replaced_by_id,
        )
    )
    result = db.execute(stmt)
    return result.rowcount == 1


def revoke(db: Session, session: RefreshSession, *, reason: RefreshSessionRevokedReason, now: datetime) -> None:
    """Idempotent: does nothing if the session is already revoked, so
    calling this from multiple places (e.g. logout racing a natural
    expiry-driven rejection) never overwrites an earlier revocation reason."""
    if session.revoked_at is not None:
        return
    stmt = (
        update(RefreshSession)
        .where(RefreshSession.id == session.id, RefreshSession.revoked_at.is_(None))
        .values(revoked_at=now, revoked_reason=reason.value)
    )
    db.execute(stmt)


def revoke_family(db: Session, family_id: uuid.UUID, *, reason: RefreshSessionRevokedReason, now: datetime) -> int:
    """Revokes every still-active session in a rotation lineage - used when
    reuse of an already-rotated token is detected, to kill the whole chain
    rather than just the one presented token."""
    stmt = (
        update(RefreshSession)
        .where(RefreshSession.family_id == family_id, RefreshSession.revoked_at.is_(None))
        .values(revoked_at=now, revoked_reason=reason.value)
    )
    result = db.execute(stmt)
    return result.rowcount


def revoke_all_for_user(db: Session, user_id: uuid.UUID, *, reason: RefreshSessionRevokedReason, now: datetime) -> int:
    """Used for account deactivation (docs/SECURITY_AND_RBAC.md section 18) -
    revokes every active session for a user regardless of family."""
    stmt = (
        update(RefreshSession)
        .where(RefreshSession.user_id == user_id, RefreshSession.revoked_at.is_(None))
        .values(revoked_at=now, revoked_reason=reason.value)
    )
    result = db.execute(stmt)
    return result.rowcount


# --- Retention / cleanup --------------------------------------------------
# See docs/SECURITY_AND_RBAC.md section 20 for the retention policy this
# implements, and scripts/cleanup_refresh_sessions.py for the maintenance
# entry point. A row is only ever eligible once it can never again be
# presented successfully (already expired, or already revoked) AND has aged
# past its retention window - a live/current session is never touched.


def _cleanup_eligibility_clause(*, now: datetime, retention_days: int, reuse_detected_retention_days: int):
    standard_cutoff = now - timedelta(days=retention_days)
    reuse_cutoff = now - timedelta(days=reuse_detected_retention_days)
    return or_(
        # Revoked for a routine reason (rotated/logout/account_deactivated),
        # aged past the standard retention window.
        and_(
            RefreshSession.revoked_at.is_not(None),
            RefreshSession.revoked_reason != RefreshSessionRevokedReason.REUSE_DETECTED.value,
            RefreshSession.revoked_at < standard_cutoff,
        ),
        # Revoked for reuse detection - kept longer for incident investigation.
        and_(
            RefreshSession.revoked_at.is_not(None),
            RefreshSession.revoked_reason == RefreshSessionRevokedReason.REUSE_DETECTED.value,
            RefreshSession.revoked_at < reuse_cutoff,
        ),
        # Never revoked, but naturally expired and aged past the standard
        # retention window (e.g. a token that was issued and simply never
        # used again - no rotation ever touched it).
        and_(
            RefreshSession.revoked_at.is_(None),
            RefreshSession.expires_at < standard_cutoff,
        ),
    )


def count_eligible_for_cleanup(db: Session, *, now: datetime, retention_days: int, reuse_detected_retention_days: int) -> int:
    stmt = select(func.count()).select_from(RefreshSession).where(
        _cleanup_eligibility_clause(
            now=now, retention_days=retention_days, reuse_detected_retention_days=reuse_detected_retention_days
        )
    )
    return db.scalar(stmt) or 0


def delete_expired_and_revoked_batch(
    db: Session,
    *,
    now: datetime,
    retention_days: int,
    reuse_detected_retention_days: int,
    batch_size: int,
) -> int:
    """Deletes up to `batch_size` eligible rows in one transaction, so a
    large accumulated backlog (e.g. the first run after a long gap) doesn't
    hold one long transaction/lock on a live database - callers should loop
    until fewer than `batch_size` rows are deleted, committing between
    batches (see app/services/auth_service.py:cleanup_expired_and_revoked_sessions).

    Any `replaced_by_id` reference to a row being deleted is nulled out
    first, in the same transaction, rather than relying on the column's
    `ON DELETE SET NULL` foreign key - that constraint is enforced on
    PostgreSQL but not by SQLite in this project's test suite (SQLite only
    enforces foreign keys when `PRAGMA foreign_keys=ON` is set), so doing it
    explicitly keeps behavior identical and correct on both.
    """
    eligible_ids = (
        select(RefreshSession.id)
        .where(
            _cleanup_eligibility_clause(
                now=now, retention_days=retention_days, reuse_detected_retention_days=reuse_detected_retention_days
            )
        )
        .limit(batch_size)
    )
    db.execute(update(RefreshSession).where(RefreshSession.replaced_by_id.in_(eligible_ids)).values(replaced_by_id=None))
    result = db.execute(delete(RefreshSession).where(RefreshSession.id.in_(eligible_ids)))
    return result.rowcount
