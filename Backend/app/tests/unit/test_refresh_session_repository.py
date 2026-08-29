import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.repositories import refresh_session_repository
from app.tests.factories import create_user
from app.utils.enums import RefreshSessionRevokedReason


def _new_session(db, user_id, *, family_id=None, expires_in_days=7):
    now = datetime.now(timezone.utc)
    return refresh_session_repository.create(
        db,
        user_id=user_id,
        family_id=family_id or uuid.uuid4(),
        token_hash=uuid.uuid4().hex + uuid.uuid4().hex,  # any unique 64-char-ish string works as a hash stand-in
        expires_at=now + timedelta(days=expires_in_days),
    )


def test_create_persists_session_with_given_id(db_session: Session) -> None:
    user = create_user(db_session, email="a@example.com")
    session_id = uuid.uuid4()

    session = refresh_session_repository.create(
        db_session,
        user_id=user.id,
        family_id=uuid.uuid4(),
        token_hash="a" * 64,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        session_id=session_id,
    )
    db_session.commit()

    assert session.id == session_id
    fetched = refresh_session_repository.get_by_token_hash(db_session, "a" * 64)
    assert fetched is not None
    assert fetched.id == session_id


def test_try_claim_for_rotation_only_succeeds_once(db_session: Session) -> None:
    user = create_user(db_session, email="b@example.com")
    session = _new_session(db_session, user.id)
    db_session.commit()

    now = datetime.now(timezone.utc)
    replaced_by_id = uuid.uuid4()

    first = refresh_session_repository.try_claim_for_rotation(db_session, session.id, replaced_by_id=replaced_by_id, now=now)
    db_session.commit()
    second = refresh_session_repository.try_claim_for_rotation(
        db_session, session.id, replaced_by_id=uuid.uuid4(), now=now
    )
    db_session.commit()

    assert first is True
    assert second is False

    db_session.refresh(session)
    assert session.revoked_at is not None
    assert session.revoked_reason == RefreshSessionRevokedReason.ROTATED.value
    assert session.replaced_by_id == replaced_by_id  # the second (losing) call must not have overwritten this


def test_revoke_is_idempotent_and_does_not_overwrite_reason(db_session: Session) -> None:
    user = create_user(db_session, email="c@example.com")
    session = _new_session(db_session, user.id)
    db_session.commit()
    now = datetime.now(timezone.utc)

    refresh_session_repository.revoke(db_session, session, reason=RefreshSessionRevokedReason.LOGOUT, now=now)
    db_session.commit()
    db_session.refresh(session)
    first_revoked_at = session.revoked_at

    # A second revoke call (e.g. a race with another revocation path) must
    # not change the reason or timestamp already recorded.
    refresh_session_repository.revoke(
        db_session, session, reason=RefreshSessionRevokedReason.ACCOUNT_DEACTIVATED, now=now + timedelta(seconds=5)
    )
    db_session.commit()
    db_session.refresh(session)

    assert session.revoked_reason == RefreshSessionRevokedReason.LOGOUT.value
    assert session.revoked_at == first_revoked_at


def test_revoke_family_only_affects_matching_family(db_session: Session) -> None:
    user = create_user(db_session, email="d@example.com")
    family_a = uuid.uuid4()
    family_b = uuid.uuid4()
    a1 = _new_session(db_session, user.id, family_id=family_a)
    a2 = _new_session(db_session, user.id, family_id=family_a)
    b1 = _new_session(db_session, user.id, family_id=family_b)
    db_session.commit()

    now = datetime.now(timezone.utc)
    count = refresh_session_repository.revoke_family(
        db_session, family_a, reason=RefreshSessionRevokedReason.REUSE_DETECTED, now=now
    )
    db_session.commit()

    assert count == 2
    for s in (a1, a2):
        db_session.refresh(s)
        assert s.revoked_at is not None
        assert s.revoked_reason == RefreshSessionRevokedReason.REUSE_DETECTED.value
    db_session.refresh(b1)
    assert b1.revoked_at is None


def test_revoke_all_for_user_spans_multiple_families(db_session: Session) -> None:
    user = create_user(db_session, email="e@example.com")
    other_user = create_user(db_session, email="f@example.com")
    s1 = _new_session(db_session, user.id)
    s2 = _new_session(db_session, user.id)
    other = _new_session(db_session, other_user.id)
    db_session.commit()

    now = datetime.now(timezone.utc)
    count = refresh_session_repository.revoke_all_for_user(
        db_session, user.id, reason=RefreshSessionRevokedReason.ACCOUNT_DEACTIVATED, now=now
    )
    db_session.commit()

    assert count == 2
    for s in (s1, s2):
        db_session.refresh(s)
        assert s.revoked_at is not None
    db_session.refresh(other)
    assert other.revoked_at is None
