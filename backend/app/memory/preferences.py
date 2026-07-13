"""Per-user preferences backed by a Redis hash.

Stores UI / analysis preferences (default chart type, preferred report format,
verbosity, etc.) per user. Values are JSON-encoded. Degrades gracefully when
Redis is unavailable.
"""

from __future__ import annotations

import json
from typing import Any

from app.core.logging import get_logger
from app.memory.redis_client import get_redis

logger = get_logger(__name__)


class UserPreferences:
    """Get/set per-user preferences, persisted in a Redis hash."""

    @staticmethod
    def _key(user_id: str) -> str:
        return f"user:{user_id}:preferences"

    async def set(self, user_id: str, key: str, value: Any) -> bool:
        """Set a single preference value (JSON-serializable)."""
        client = get_redis()
        if client is None:
            return False
        try:
            await client.hset(self._key(user_id), key, json.dumps(value))
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("preferences_set_failed", user_id=user_id, error=str(exc))
            return False

    async def get(self, user_id: str, key: str, default: Any | None = None) -> Any | None:
        """Return a preference value or ``default`` if absent/unavailable."""
        client = get_redis()
        if client is None:
            return default
        try:
            raw = await client.hget(self._key(user_id), key)
            return json.loads(raw) if raw is not None else default
        except Exception as exc:  # noqa: BLE001
            logger.warning("preferences_get_failed", user_id=user_id, error=str(exc))
            return default

    async def all(self, user_id: str) -> dict[str, Any]:
        """Return all preferences for a user as a decoded dict."""
        client = get_redis()
        if client is None:
            return {}
        try:
            raw = await client.hgetall(self._key(user_id))
            result: dict[str, Any] = {}
            for key, value in (raw or {}).items():
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[key] = value
            return result
        except Exception as exc:  # noqa: BLE001
            logger.warning("preferences_all_failed", user_id=user_id, error=str(exc))
            return {}

    async def update(self, user_id: str, values: dict[str, Any]) -> bool:
        """Bulk-set multiple preferences at once."""
        client = get_redis()
        if client is None or not values:
            return False
        try:
            mapping = {k: json.dumps(v) for k, v in values.items()}
            await client.hset(self._key(user_id), mapping=mapping)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("preferences_update_failed", user_id=user_id, error=str(exc))
            return False


__all__ = ["UserPreferences"]
