from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.tests.factories import create_user


def test_register_creates_citizen_account(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "citizen1@example.com",
            "password": "CitizenPass1!",
            "full_name": "Citizen One",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["role"] == "citizen"
    assert body["email"] == "citizen1@example.com"
    assert body["district_id"] is None


def test_register_ignores_client_supplied_role(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "escalator@example.com",
            "password": "CitizenPass1!",
            "full_name": "Would Be Admin",
            "role": "admin",
        },
    )

    assert response.status_code == 201
    assert response.json()["role"] == "citizen"


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    payload = {
        "email": "dup@example.com",
        "password": "CitizenPass1!",
        "full_name": "Dup User",
    }
    first = client.post("/api/v1/auth/register", json=payload)
    second = client.post("/api/v1/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "USER_ALREADY_EXISTS"


def test_login_succeeds_with_correct_credentials(client: TestClient, db_session: Session) -> None:
    create_user(db_session, email="login@example.com", password="LoginPass1!")

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "LoginPass1!"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["user"]["email"] == "login@example.com"


def test_login_rejects_wrong_password(client: TestClient, db_session: Session) -> None:
    create_user(db_session, email="wrongpass@example.com", password="LoginPass1!")

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpass@example.com", "password": "IncorrectPass1!"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_rejects_inactive_account(client: TestClient, db_session: Session) -> None:
    create_user(db_session, email="inactive@example.com", password="LoginPass1!", is_active=False)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@example.com", "password": "LoginPass1!"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACCOUNT_INACTIVE"


def test_me_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_me_returns_current_user(client: TestClient, db_session: Session) -> None:
    create_user(db_session, email="me@example.com", password="LoginPass1!")
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "me@example.com", "password": "LoginPass1!"},
    )
    access_token = login.json()["access_token"]

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


def test_refresh_issues_new_access_token(client: TestClient, db_session: Session) -> None:
    create_user(db_session, email="refresh@example.com", password="LoginPass1!")
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@example.com", "password": "LoginPass1!"},
    )
    refresh_token = login.json()["refresh_token"]

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_refresh_rejects_access_token(client: TestClient, db_session: Session) -> None:
    create_user(db_session, email="wrongtype@example.com", password="LoginPass1!")
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "wrongtype@example.com", "password": "LoginPass1!"},
    )
    access_token = login.json()["access_token"]

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


def test_invalid_bearer_token_is_rejected(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"})

    assert response.status_code == 401
