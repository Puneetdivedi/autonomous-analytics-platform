"""Integration tests for the authentication API."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_register_login_me_flow(client: AsyncClient) -> None:
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "alice@eaap.io", "password": "Password123", "full_name": "Alice"},
    )
    assert reg.status_code in (200, 201), reg.text

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "alice@eaap.io", "password": "Password123"},
    )
    assert login.status_code == 200, login.text
    tokens = login.json()
    assert tokens["access_token"] and tokens["refresh_token"]

    me = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json()["email"] == "alice@eaap.io"


async def test_login_wrong_password(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "bob@eaap.io", "password": "Password123"},
    )
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "bob@eaap.io", "password": "nope"}
    )
    assert resp.status_code == 401


async def test_me_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
