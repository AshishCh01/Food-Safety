import uuid
from datetime import timedelta

import pytest

from app.core.security import (
    TokenType,
    _create_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
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


def test_refresh_token_cannot_be_used_as_access_token() -> None:
    user_id = uuid.uuid4()
    refresh_token = create_refresh_token(user_id)

    with pytest.raises(InvalidTokenError):
        decode_token(refresh_token, TokenType.ACCESS)


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
