import uuid
from datetime import timedelta

import pytest

from app.core.security import (
    TokenType,
    _create_token,
    create_access_token,
    decode_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.utils.exceptions import InvalidTokenError


def test_hash_password_does_not_store_plaintext() -> None:
    password_hash = hash_password("SuperSecret1!")

    assert password_hash != "SuperSecret1!"
    assert verify_password("SuperSecret1!", password_hash)


def test_verify_password_rejects_wrong_password() -> None:
    password_hash = hash_password("SuperSecret1!")

    assert verify_password("WrongPassword1!", password_hash) is False


def test_access_token_round_trip_contains_claims() -> None:
    user_id = uuid.uuid4()
    district_id = uuid.uuid4()

    token = create_access_token(user_id, "district_officer", district_id, True)
    payload = decode_token(token, TokenType.ACCESS)

    assert payload["sub"] == str(user_id)
    assert payload["role"] == "district_officer"
    assert payload["district_id"] == str(district_id)
    assert payload["status"] == "active"
    assert payload["type"] == "access"


def test_access_token_carries_session_id_claim() -> None:
    user_id = uuid.uuid4()
    session_id = uuid.uuid4()

    token = create_access_token(user_id, "citizen", None, True, session_id=session_id)
    payload = decode_token(token, TokenType.ACCESS)

    assert payload["sid"] == str(session_id)


def test_access_token_session_id_defaults_to_none() -> None:
    user_id = uuid.uuid4()

    token = create_access_token(user_id, "citizen", None, True)
    payload = decode_token(token, TokenType.ACCESS)

    assert payload["sid"] is None


def test_opaque_refresh_token_is_not_a_jwt() -> None:
    # Refresh tokens are opaque random strings, not JWTs - a plain
    # `decode_token` call on one must fail instead of accidentally parsing.
    token = generate_refresh_token()

    with pytest.raises(InvalidTokenError):
        decode_token(token, TokenType.ACCESS)


def test_refresh_token_generation_is_unique_and_high_entropy() -> None:
    tokens = {generate_refresh_token() for _ in range(100)}

    assert len(tokens) == 100
    assert all(len(t) >= 48 for t in tokens)


def test_refresh_token_hash_is_deterministic_and_not_reversible_lookalike() -> None:
    token = generate_refresh_token()

    assert hash_refresh_token(token) == hash_refresh_token(token)
    assert hash_refresh_token(token) != token
    assert len(hash_refresh_token(token)) == 64  # sha256 hex digest


def test_expired_token_is_rejected() -> None:
    user_id = uuid.uuid4()
    expired_token = _create_token(user_id, TokenType.ACCESS, timedelta(seconds=-1))

    with pytest.raises(InvalidTokenError):
        decode_token(expired_token, TokenType.ACCESS)


def test_tampered_token_is_rejected() -> None:
    user_id = uuid.uuid4()
    token = create_access_token(user_id, "citizen", None, True)

    with pytest.raises(InvalidTokenError):
        decode_token(token + "tampered", TokenType.ACCESS)
