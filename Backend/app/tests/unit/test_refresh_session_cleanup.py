"""Retention/cleanup policy for refresh_sessions - docs/SECURITY_AND_RBAC.md
section 20. Covers both the repository-level eligibility query/batching and
the service-level policy (which retention window applies to which
revocation reason) and looping/commit behavior."""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refresh_session import RefreshSession
from app.repositories import refresh_session_repository
from app.services import auth_service
from app.tests.factories import create_user
from app.utils.enums import RefreshSessionRevokedReason

STANDARD_DAYS = 7
REUSE_DAYS = 90


def _still_exists(db: Session, session_id) -> bool:
    # Deliberately not refresh_session_repository.get_by_id (db.get()):
    # when the row being checked is still present in this session's
    # identity map from having been created earlier in the same test, a
    # raw Core DELETE elsewhere doesn't clear that cache entry, and
    # db.get() would try to refresh the (now expired-by-commit) cached
    # object and raise ObjectDeletedError instead of returning None. A
    # plain SELECT has no such ambiguity: zero rows back means gone.
    stmt = select(RefreshSession.id).where(RefreshSession.id == session_id)
    return db.execute(stmt).scalar_one_or_none() is not None


def _make_session(
    db: Session,
    user_id,
    *,
    family_id=None,
    expires_at=None,
    revoked_at=None,
    revoked_reason=None,
    replaced_by_id=None,
) -> RefreshSession:
    now = datetime.now(timezone.utc)
    session = RefreshSession(
        user_id=user_id,
        family_id=family_id or uuid.uuid4(),
        token_hash=uuid.uuid4().hex + uuid.uuid4().hex,
        expires_at=expires_at or (now + timedelta(days=7)),
        revoked_at=revoked_at,
        revoked_reason=revoked_reason,
        replaced_by_id=replaced_by_id,
    )
    db.add(session)
    db.flush()
    return session


def _count(db: Session, now) -> int:
    return refresh_session_repository.count_eligible_for_cleanup(
        db, now=now, retention_days=STANDARD_DAYS, reuse_detected_retention_days=REUSE_DAYS
    )


def _delete_batch(db: Session, now, batch_size=1000) -> int:
    return refresh_session_repository.delete_expired_and_revoked_batch(
        db, now=now, retention_days=STANDARD_DAYS, reuse_detected_retention_days=REUSE_DAYS, batch_size=batch_size
    )


def test_live_session_is_never_eligible(db_session: Session) -> None:
    user = create_user(db_session, email="live@example.com")
    now = datetime.now(timezone.utc)
    _make_session(db_session, user.id, expires_at=now + timedelta(days=7))
    db_session.commit()

    assert _count(db_session, now) == 0
    assert _delete_batch(db_session, now) == 0


def test_recently_expired_session_is_not_yet_eligible(db_session: Session) -> None:
    user = create_user(db_session, email="recent-expired@example.com")
    now = datetime.now(timezone.utc)
    _make_session(db_session, user.id, expires_at=now - timedelta(days=1))
    db_session.commit()

    assert _count(db_session, now) == 0


def test_expired_session_past_retention_is_eligible(db_session: Session) -> None:
    user = create_user(db_session, email="old-expired@example.com")
    now = datetime.now(timezone.utc)
    session = _make_session(db_session, user.id, expires_at=now - timedelta(days=STANDARD_DAYS + 1))
    session_id = session.id  # captured before commit expires the object's attributes
    db_session.commit()

    assert _count(db_session, now) == 1
    deleted = _delete_batch(db_session, now)
    assert deleted == 1
    assert not _still_exists(db_session, session_id)


def test_recently_revoked_session_is_not_yet_eligible(db_session: Session) -> None:
    user = create_user(db_session, email="recent-revoked@example.com")
    now = datetime.now(timezone.utc)
    _make_session(
        db_session,
        user.id,
        revoked_at=now - timedelta(days=1),
        revoked_reason=RefreshSessionRevokedReason.ROTATED.value,
    )
    db_session.commit()

    assert _count(db_session, now) == 0


def test_routinely_revoked_session_past_standard_retention_is_eligible(db_session: Session) -> None:
    user = create_user(db_session, email="rotated-old@example.com")
    now = datetime.now(timezone.utc)
    for reason in (
        RefreshSessionRevokedReason.ROTATED.value,
        RefreshSessionRevokedReason.LOGOUT.value,
        RefreshSessionRevokedReason.ACCOUNT_DEACTIVATED.value,
    ):
        _make_session(db_session, user.id, revoked_at=now - timedelta(days=STANDARD_DAYS + 1), revoked_reason=reason)
    db_session.commit()

    assert _count(db_session, now) == 3
    assert _delete_batch(db_session, now) == 3


def test_reuse_detected_session_gets_extended_retention(db_session: Session) -> None:
    """A reuse-detected revocation must survive the standard retention
    window - it's the strongest security signal and the most valuable to
    keep for incident investigation - but still be cleaned up eventually."""
    user = create_user(db_session, email="reuse-window@example.com")
    now = datetime.now(timezone.utc)
    session = _make_session(
        db_session,
        user.id,
        revoked_at=now - timedelta(days=STANDARD_DAYS + 5),  # past standard, not past reuse-specific
        revoked_reason=RefreshSessionRevokedReason.REUSE_DETECTED.value,
    )
    db_session.commit()

    assert _count(db_session, now) == 0
    assert _delete_batch(db_session, now) == 0

    # Backdate it further, past the extended window, and confirm it's now eligible.
    session.revoked_at = now - timedelta(days=REUSE_DAYS + 1)
    db_session.commit()

    assert _count(db_session, now) == 1
    assert _delete_batch(db_session, now) == 1


def test_deleting_a_session_nulls_out_references_that_replaced_it(db_session: Session) -> None:
    """replaced_by_id on an OLDER session can point at the row being
    deleted (e.g. session A was replaced by session B; A ages out and gets
    cleaned up while B is still the live, current session referenced from
    nothing itself). Deletion must not leave a dangling reference nor error
    out, regardless of whether the database enforces the FK's
    ON DELETE SET NULL (SQLite in this test suite does not, by default)."""
    user = create_user(db_session, email="chain@example.com")
    now = datetime.now(timezone.utc)
    family = uuid.uuid4()

    newest = _make_session(db_session, user.id, family_id=family, expires_at=now + timedelta(days=7))
    db_session.flush()
    newest_id = newest.id  # captured before commit expires the object's attributes
    oldest = _make_session(
        db_session,
        user.id,
        family_id=family,
        revoked_at=now - timedelta(days=STANDARD_DAYS + 1),
        revoked_reason=RefreshSessionRevokedReason.ROTATED.value,
        replaced_by_id=newest_id,
    )
    oldest_id = oldest.id
    db_session.commit()

    deleted = _delete_batch(db_session, now)

    assert deleted == 1
    assert not _still_exists(db_session, oldest_id)
    # The still-live session must be untouched and unaffected.
    surviving_revoked_at = db_session.execute(
        select(RefreshSession.revoked_at).where(RefreshSession.id == newest_id)
    ).scalar_one()
    assert surviving_revoked_at is None


def test_delete_batch_respects_batch_size_and_is_resumable(db_session: Session) -> None:
    user = create_user(db_session, email="batching@example.com")
    now = datetime.now(timezone.utc)
    old_enough = now - timedelta(days=STANDARD_DAYS + 1)
    for _ in range(5):
        _make_session(db_session, user.id, revoked_at=old_enough, revoked_reason=RefreshSessionRevokedReason.LOGOUT.value)
    db_session.commit()

    first_batch = _delete_batch(db_session, now, batch_size=2)
    db_session.commit()
    assert first_batch == 2
    assert _count(db_session, now) == 3

    second_batch = _delete_batch(db_session, now, batch_size=2)
    db_session.commit()
    assert second_batch == 2
    assert _count(db_session, now) == 1

    third_batch = _delete_batch(db_session, now, batch_size=2)
    assert third_batch == 1
    assert _count(db_session, now) == 0


def test_service_cleanup_loops_across_batches_and_returns_total(db_session: Session) -> None:
    user = create_user(db_session, email="service-batching@example.com")
    now = datetime.now(timezone.utc)
    old_enough = now - timedelta(days=STANDARD_DAYS + 1)
    for _ in range(7):
        _make_session(db_session, user.id, revoked_at=old_enough, revoked_reason=RefreshSessionRevokedReason.LOGOUT.value)
    db_session.commit()

    total = auth_service.cleanup_expired_and_revoked_sessions(db_session, batch_size=3)

    assert total == 7
    assert auth_service.count_sessions_eligible_for_cleanup(db_session) == 0


def test_service_count_matches_repository_count(db_session: Session) -> None:
    user = create_user(db_session, email="service-count@example.com")
    now = datetime.now(timezone.utc)
    _make_session(db_session, user.id, expires_at=now + timedelta(days=1))  # live, not counted
    _make_session(
        db_session,
        user.id,
        revoked_at=now - timedelta(days=STANDARD_DAYS + 1),
        revoked_reason=RefreshSessionRevokedReason.LOGOUT.value,
    )
    db_session.commit()

    assert auth_service.count_sessions_eligible_for_cleanup(db_session) == 1
