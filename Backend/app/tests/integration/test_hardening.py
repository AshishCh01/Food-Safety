"""Phase 12 cross-cutting hardening: rate limiting, the catch-all error
envelope, and baseline security headers. See also app/tests/unit/test_evidence_validation.py
(upload hardening) and app/tests/integration/test_assignments.py (assignment
race handling)."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.rate_limit import InMemoryRateLimiter, login_rate_limiter
from app.tests.factories import create_user


def test_security_headers_present_on_every_response(client: TestClient) -> None:
    response = client.get("/health")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"


def test_unhandled_exception_returns_consistent_error_envelope(client: TestClient, monkeypatch) -> None:
    from app.api.auth import router as auth_router

    def _boom(db, email, password):
        raise RuntimeError("simulated unexpected failure")

    monkeypatch.setattr(auth_router.auth_service, "authenticate", _boom)

    # error_handling_middleware (app/main.py) catches this itself and
    # returns a normal Response, so the exception never escapes the ASGI
    # app - no need to disable TestClient's raise_server_exceptions here.
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "x@example.com", "password": "whatever"},
        headers={"Origin": "http://localhost:5173"},
    )

    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert "simulated unexpected failure" not in body["error"]["message"]
    assert body["error"]["details"] is None


def test_unhandled_exception_response_still_has_cors_and_security_headers(client: TestClient, monkeypatch) -> None:
    """Regression test for a subtlety in how Starlette wires up exception
    handling: a handler registered for the bare `Exception` type
    (`@app.exception_handler(Exception)`) gets moved into
    ServerErrorMiddleware, which sits OUTSIDE every user middleware
    including CORSMiddleware - so relying on it alone would send an
    unhandled-exception response with no CORS headers, and a cross-origin
    browser caller (the React frontend) would see an opaque CORS/network
    failure instead of the JSON error body. error_handling_middleware in
    app/main.py catches the exception itself, inside CORSMiddleware, so this
    must not regress."""
    from app.api.auth import router as auth_router

    def _boom(db, email, password):
        raise RuntimeError("simulated unexpected failure")

    monkeypatch.setattr(auth_router.auth_service, "authenticate", _boom)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "x@example.com", "password": "whatever"},
        headers={"Origin": "http://localhost:5173"},
    )

    assert response.status_code == 500
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_login_is_rate_limited_after_repeated_attempts(client: TestClient, db_session: Session) -> None:
    create_user(db_session, email="ratelimited@example.com", password="CorrectPass1!")

    responses = [
        client.post(
            "/api/v1/auth/login",
            json={"email": "ratelimited@example.com", "password": "WrongPassword!"},
        )
        for _ in range(login_rate_limiter.max_requests + 1)
    ]

    assert all(r.status_code == 401 for r in responses[:-1])
    assert responses[-1].status_code == 429
    assert responses[-1].json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"


def test_register_is_rate_limited_after_repeated_attempts(client: TestClient) -> None:
    from app.core.rate_limit import register_rate_limiter

    responses = [
        client.post(
            "/api/v1/auth/register",
            json={
                "email": f"spam{i}@example.com",
                "password": "CitizenPass1!",
                "full_name": "Spammer",
            },
        )
        for i in range(register_rate_limiter.max_requests + 1)
    ]

    assert responses[-1].status_code == 429


def test_rate_limiter_windows_are_independent_per_key() -> None:
    limiter = InMemoryRateLimiter(max_requests=2, window_seconds=60)

    limiter.check("ip-a")
    limiter.check("ip-a")
    limiter.check("ip-b")  # a different key must not share ip-a's quota

    import pytest

    from app.utils.exceptions import RateLimitExceededError

    with pytest.raises(RateLimitExceededError):
        limiter.check("ip-a")
