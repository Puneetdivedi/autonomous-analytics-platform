"""Memory package.

Layered memory for the analytics agents:

* :class:`ConversationMemory` — short-term recent messages per chat (Redis list).
* :class:`ProjectMemory` — durable project facts / schema summaries (Redis hash).
* :class:`UserPreferences` — per-user settings (Redis hash).
* :class:`LongTermMemory` — semantic recall over Qdrant with offline fallback.

All backends degrade gracefully when Redis/Qdrant are unavailable.
"""

from __future__ import annotations

from app.memory.conversation import ConversationMemory
from app.memory.long_term import LongTermMemory
from app.memory.preferences import UserPreferences
from app.memory.project import ProjectMemory
from app.memory.redis_client import close_redis, get_redis, ping

__all__ = [
    "ConversationMemory",
    "ProjectMemory",
    "UserPreferences",
    "LongTermMemory",
    "get_redis",
    "ping",
    "close_redis",
]
