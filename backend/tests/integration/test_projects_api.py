"""Integration tests for the projects API."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_create_and_list_projects(client: AsyncClient, auth_headers: dict) -> None:
    created = await client.post(
        "/api/v1/projects",
        json={"name": "Revenue Analysis", "description": "Q3 revenue"},
        headers=auth_headers,
    )
    assert created.status_code in (200, 201), created.text
    project = created.json()
    assert project["name"] == "Revenue Analysis"

    listed = await client.get("/api/v1/projects", headers=auth_headers)
    assert listed.status_code == 200
    names = [p["name"] for p in listed.json()]
    assert "Revenue Analysis" in names


async def test_projects_require_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/projects")
    assert resp.status_code == 401
