"""Cached async Redis client.

Provides a lazily-constructed, module-level :class:`redis.asyncio.Redis` client
built from ``settings.redis_url``. The client is created eagerly but connects
lazily on first command, so importing this module never blocks or fails when
Redis is down — callers degrade gracefully via :func:`ping`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.config import settings
from app.core.logging import get_logger

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = get_logger(__name__)

_client: Redis | None = None


def get_redis() -> Redis | None:
    """Return the shared async Redis client, or ``None`` if construction fails."""
    global _client
    if _client is not None:
        return _client
    try:
        from redis.asyncio import Redis

        _client = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        logger.info("redis_client_created", url=settings.redis_url)
        return _client
    except Exception as exc:  # noqa: BLE001
        logger.warning("redis_client_unavailable", error=str(exc))
        return None


async def ping() -> bool:
    """Return ``True`` if Redis responds to PING, else ``False`` (never raises)."""
    client = get_redis()
    if client is None:
        return False
    try:
        return bool(await client.ping())
    except Exception as exc:  # noqa: BLE001
        logger.warning("redis_ping_failed", error=str(exc))
        return False


async def close_redis() -> None:
    """Close and reset the shared client (for shutdown / tests)."""
    global _client
    if _client is not None:
        try:
            await _client.aclose()
        except Exception as exc:  # noqa: BLE001
            logger.warning("redis_close_failed", error=str(exc))
        finally:
            _client = None


__all__ = ["get_redis", "ping", "close_redis"]
