"""Short-term conversation memory backed by Redis lists.

Stores the most recent messages per chat as JSON entries in a capped Redis
list. All operations degrade to no-ops / empty results when Redis is
unavailable so the app keeps working without a cache.
"""

from __future__ import annotations

import json
import time
from typing import Any

from app.core.logging import get_logger
from app.memory.redis_client import get_redis

logger = get_logger(__name__)


class ConversationMemory:
    """Recent-message buffer for a chat, stored in a capped Redis list."""

    def __init__(self, *, max_messages: int = 50, ttl_seconds: int = 60 * 60 * 24) -> None:
        self._max = max_messages
        self._ttl = ttl_seconds

    @staticmethod
    def _key(chat_id: str) -> str:
        return f"chat:{chat_id}:messages"

    async def append(self, chat_id: str, role: str, content: str) -> bool:
        """Append a message; trims the list to ``max_messages``. Returns success."""
        client = get_redis()
        if client is None:
            return False
        entry = json.dumps({"role": role, "content": content, "ts": time.time()})
        key = self._key(chat_id)
        try:
            pipe = client.pipeline()
            pipe.rpush(key, entry)
            pipe.ltrim(key, -self._max, -1)
            pipe.expire(key, self._ttl)
            await pipe.execute()
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("conversation_append_failed", chat_id=chat_id, error=str(exc))
            return False

    async def recent(self, chat_id: str, n: int = 10) -> list[dict[str, Any]]:
        """Return up to the last ``n`` messages (oldest first)."""
        client = get_redis()
        if client is None:
            return []
        try:
            raw = await client.lrange(self._key(chat_id), -n, -1)
            messages: list[dict[str, Any]] = []
            for item in raw:
                try:
                    messages.append(json.loads(item))
                except (json.JSONDecodeError, TypeError):
                    continue
            return messages
        except Exception as exc:  # noqa: BLE001
            logger.warning("conversation_recent_failed", chat_id=chat_id, error=str(exc))
            return []

    async def clear(self, chat_id: str) -> bool:
        """Delete all stored messages for a chat."""
        client = get_redis()
        if client is None:
            return False
        try:
            await client.delete(self._key(chat_id))
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("conversation_clear_failed", chat_id=chat_id, error=str(exc))
            return False


__all__ = ["ConversationMemory"]
