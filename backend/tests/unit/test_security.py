"""Unit tests for password hashing and JWT handling."""

from __future__ import annotations

import pytest

from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

pytestmark = pytest.mark.unit


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("Secret123")
    assert hashed != "Secret123"
    assert verify_password("Secret123", hashed)
    assert not verify_password("wrong", hashed)


def test_access_token_encodes_role() -> None:
    token = create_access_token("user-1", role="analyst")
    payload = decode_token(token, expected_type="access")
    assert payload["sub"] == "user-1"
    assert payload["role"] == "analyst"
    assert payload["type"] == "access"


def test_wrong_token_type_rejected() -> None:
    refresh = create_refresh_token("user-1")
    with pytest.raises(AuthenticationError):
        decode_token(refresh, expected_type="access")


def test_tampered_token_rejected() -> None:
    with pytest.raises(AuthenticationError):
        decode_token("not.a.jwt", expected_type="access")
