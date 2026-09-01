"""Server-side refresh-token session management (docs/SECURITY_AND_RBAC.md
section 18): rotation, reuse detection, logout revocation, and account
deactivation revocation. See also app/tests/unit/test_refresh_session_repository.py
(repository-level concurrency primitives) and app/tests/unit/test_security.py
(token generation/hashing)."""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_refresh_token
from app.repositories import refresh_session_repository
from app.tests.factories import auth_headers, create_user
from app.utils.enums import RefreshSessionRevokedReason, UserRole


def _admin_headers(db_session: Session) -> dict:
    admin = create_user(db_session, email="sessions-admin@example.com", role=UserRole.ADMIN)
    return auth_headers(admin)


def test_login_creates_a_refresh_session(client: TestClient, db_session: Session) -> None:
    create_user(db_session, email="login-session@example.com", password="LoginPass1!")

    response = client.post(
        "/api/v1/auth/login", json={"email": "login-session@example.com", "password": "LoginPass1!"}
    )

    assert response.status_code == 200
    refresh_token = response.json()["refresh_token"]
    session = refresh_session_repository.get_by_token_hash(db_session, hash_refresh_token(refresh_token))
    assert session is not None
    assert session.revoked_at is None


def test_refresh_returns_a_rotated_token_pair(client: TestClient, db_session: Session) -> None:
    create_user(db_session, email="rotate@example.com", password="LoginPass1!")
    login = client.post("/api/v1/auth/login", json={"email": "rotate@example.com", "password": "LoginPass1!"})
    original_refresh = login.json()["refresh_token"]
    original_access = login.json()["access_token"]

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": original_refresh})

    assert response.status_code == 200
    body = response.json()
    assert body["refresh_token"] != original_refresh
    assert body["access_token"] != original_access

    old_session = refresh_session_repository.get_by_token_hash(db_session, hash_refresh_token(original_refresh))
    new_session = refresh_session_repository.get_by_token_hash(db_session, hash_refresh_token(body["refresh_token"]))
    assert old_session.revoked_at is not None
    assert old_session.revoked_reason == RefreshSessionRevokedReason.ROTATED.value
    assert old_session.replaced_by_id == new_session.id
    assert new_session.revoked_at is None
    assert new_session.family_id == old_session.family_id  # same lineage


def test_old_refresh_token_rejected_after_rotation(client: TestClient, db_session: Session) -> None:
    create_user(db_session, email="stale@example.com", password="LoginPass1!")
    login = client.post("/api/v1/auth/login", json={"email": "stale@example.com", "password": "LoginPass1!"})
    original_refresh = login.json()["refresh_token"]
    client.post("/api/v1/auth/refresh", json={"refresh_token": original_refresh})

    reuse_attempt = client.post("/api/v1/auth/refresh", json={"refresh_token": original_refresh})

    assert reuse_attempt.status_code == 401
    assert reuse_attempt.json()["error"]["code"] == "INVALID_TOKEN"


def test_refresh_token_reuse_beyond_grace_window_revokes_whole_family(client: TestClient, db_session: Session) -> None:
    create_user(db_session, email="replay@example.com", password="LoginPass1!")
    login = client.post("/api/v1/auth/login", json={"email": "replay@example.com", "password": "LoginPass1!"})
    original_refresh = login.json()["refresh_token"]

    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": original_refresh})
    current_refresh = rotated.json()["refresh_token"]

    # Simulate the rotation having happened well outside the benign-race
    # grace window, so a later presentation of the old token reads as replay
    # of a stale, already-superseded token rather than a near-simultaneous
    # concurrent request.
    old_session = refresh_session_repository.get_by_token_hash(db_session, hash_refresh_token(original_refresh))
    old_session.revoked_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    db_session.commit()

    replay_attempt = client.post("/api/v1/auth/refresh", json={"refresh_token": original_refresh})
    assert replay_attempt.status_code == 401

    # The whole family - including the token that was legitimately current
    # a moment ago - must now be dead.
    follow_up = client.post("/api/v1/auth/refresh", json={"refresh_token": current_refresh})
    assert follow_up.status_code == 401

    current_session = refresh_session_repository.get_by_token_hash(db_session, hash_refresh_token(current_refresh))
    assert current_session.revoked_at is not None
    assert current_session.revoked_reason == RefreshSessionRevokedReason.REUSE_DETECTED.value


def test_concurrent_refresh_second_caller_loses_without_cascading(client: TestClient, db_session: Session) -> None:
    """Two near-simultaneous requests presenting the same still-valid
    refresh token: exactly one wins the rotation, the other is rejected, and
    - because this happens within the reuse-detection grace window - the
    winner's new token pair must remain fully usable (no family-wide
    revocation triggered by what is really just benign concurrency)."""
    create_user(db_session, email="concurrent@example.com", password="LoginPass1!")
    login = client.post("/api/v1/auth/login", json={"email": "concurrent@example.com", "password": "LoginPass1!"})
    original_refresh = login.json()["refresh_token"]

    first = client.post("/api/v1/auth/refresh", json={"refresh_token": original_refresh})
    second = client.post("/api/v1/auth/refresh", json={"refresh_token": original_refresh})

    assert first.status_code == 200
    assert second.status_code == 401

    winners_new_refresh = first.json()["refresh_token"]
    follow_up = client.post("/api/v1/auth/refresh", json={"refresh_token": winners_new_refresh})
    assert follow_up.status_code == 200


def test_logout_revokes_current_session(client: TestClient, db_session: Session) -> None:
    create_user(db_session, email="logout@example.com", password="LoginPass1!")
    login = client.post("/api/v1/auth/login", json={"email": "logout@example.com", "password": "LoginPass1!"})
    access_token = login.json()["access_token"]
    refresh_token = login.json()["refresh_token"]

    logout_response = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {access_token}"})
    assert logout_response.status_code == 200

    refresh_after_logout = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_after_logout.status_code == 401

    session = refresh_session_repository.get_by_token_hash(db_session, hash_refresh_token(refresh_token))
    assert session.revoked_reason == RefreshSessionRevokedReason.LOGOUT.value


def test_logout_tolerates_access_token_without_session_claim(client: TestClient, db_session: Session) -> None:
    user = create_user(db_session, email="no-sid@example.com")
    # A token minted without session_id, e.g. representing one issued before
    # this feature existed - logout must still succeed rather than error.
    legacy_style_token = create_access_token(user.id, user.role.value, None, user.is_active)

    response = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {legacy_style_token}"})

    assert response.status_code == 200


def test_expired_refresh_token_is_rejected(client: TestClient, db_session: Session) -> None:
    user = create_user(db_session, email="expired@example.com")
    plaintext = "expired-token-value-for-testing-purposes-only"
    refresh_session_repository.create(
        db_session,
        user_id=user.id,
        family_id=uuid.uuid4(),
        token_hash=hash_refresh_token(plaintext),
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db_session.commit()

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": plaintext})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


def test_unknown_refresh_token_is_rejected(client: TestClient) -> None:
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-real-token-at-all"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


def test_account_deactivation_revokes_refresh_sessions(client: TestClient, db_session: Session) -> None:
    create_user(db_session, email="soon-deactivated@example.com", password="LoginPass1!")
    login = client.post(
        "/api/v1/auth/login", json={"email": "soon-deactivated@example.com", "password": "LoginPass1!"}
    )
    refresh_token = login.json()["refresh_token"]
    target_user_id = login.json()["user"]["id"]

    deactivate = client.patch(
        f"/api/v1/admin/users/{target_user_id}/status",
        headers=_admin_headers(db_session),
        json={"is_active": False},
    )
    assert deactivate.status_code == 200
    assert deactivate.json()["is_active"] is False

    refresh_after_deactivation = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_after_deactivation.status_code == 401

    session = refresh_session_repository.get_by_token_hash(db_session, hash_refresh_token(refresh_token))
    assert session.revoked_reason == RefreshSessionRevokedReason.ACCOUNT_DEACTIVATED.value


def test_reactivated_account_still_needs_a_fresh_login(client: TestClient, db_session: Session) -> None:
    """Deactivation revokes existing sessions permanently - reactivating the
    account does not resurrect them, since they were deliberately revoked
    rather than merely gated on a live is_active check."""
    create_user(db_session, email="cycle@example.com", password="LoginPass1!")
    login = client.post("/api/v1/auth/login", json={"email": "cycle@example.com", "password": "LoginPass1!"})
    refresh_token = login.json()["refresh_token"]
    target_user_id = login.json()["user"]["id"]
    admin_headers = _admin_headers(db_session)

    client.patch(f"/api/v1/admin/users/{target_user_id}/status", headers=admin_headers, json={"is_active": False})
    client.patch(f"/api/v1/admin/users/{target_user_id}/status", headers=admin_headers, json={"is_active": True})

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 401


def test_refresh_flow_preserves_authorization_and_rbac(client: TestClient, db_session: Session) -> None:
    """Regression check: a rotated access token still authenticates
    normally, and role enforcement is unaffected by the session-management
    changes."""
    create_user(db_session, email="regression-citizen@example.com", password="LoginPass1!")
    login = client.post(
        "/api/v1/auth/login", json={"email": "regression-citizen@example.com", "password": "LoginPass1!"}
    )
    refresh_token = login.json()["refresh_token"]

    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    new_access_token = rotated.json()["access_token"]

    me_response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_access_token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "regression-citizen@example.com"

    # A citizen must still be denied admin-only functionality after refresh.
    admin_probe = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {new_access_token}"})
    assert admin_probe.status_code == 403
