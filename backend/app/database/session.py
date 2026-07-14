"""Async database engine and session management."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings


def _prepare(url: str) -> tuple[str, dict[str, Any]]:
    """Normalize a Postgres DSN for asyncpg.

    asyncpg (unlike libpq) rejects ``sslmode``/``channel_binding`` query args, so
    we strip them and translate an SSL requirement (as Neon/Supabase emit) into
    asyncpg's ``ssl`` connect arg.
    """
    connect_args: dict[str, Any] = {}
    if url.startswith("postgresql+asyncpg"):
        parts = urlsplit(url)
        query = dict(parse_qsl(parts.query))
        sslmode = query.pop("sslmode", None)
        query.pop("channel_binding", None)
        if sslmode and sslmode != "disable":
            connect_args["ssl"] = True
        url = urlunsplit(parts._replace(query=urlencode(query)))
    return url, connect_args


_url, _connect_args = _prepare(settings.database_url)
_engine_kwargs: dict[str, Any] = {"echo": False, "future": True, "connect_args": _connect_args}
# On serverless (Vercel), avoid a long-lived pool that would exhaust the DB's
# connection limit across many short-lived function instances.
if os.environ.get("VERCEL"):
    _engine_kwargs["poolclass"] = NullPool
else:
    _engine_kwargs["pool_pre_ping"] = True

engine: AsyncEngine = create_async_engine(_url, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a transactional session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
