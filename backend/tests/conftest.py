"""Shared pytest fixtures: isolated SQLite DB, app, and async HTTP client."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("LANGFUSE_ENABLED", "false")
os.environ.setdefault("ENVIRONMENT", "development")

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

import app.models  # noqa: E402,F401  (populate metadata)
from app.database.base import Base  # noqa: E402
from app.database.session import get_db  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402


@pytest_asyncio.fixture
async def engine() -> AsyncIterator:
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def client(session_factory) -> AsyncIterator[AsyncClient]:
    async def _override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Register + login a user, returning Authorization headers."""
    email = "tester@eaap.io"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123", "full_name": "Tester"},
    )
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
