"""Project-level memory backed by a Redis hash.

Stores durable, project-scoped facts and schema summaries (e.g. introspected
table schemas, domain glossary) as fields in a per-project Redis hash. Values
are JSON-encoded. Degrades gracefully when Redis is unavailable.
"""

from __future__ import annotations

import json
from typing import Any

from app.core.logging import get_logger
from app.memory.redis_client import get_redis

logger = get_logger(__name__)


class ProjectMemory:
    """Key/value store of project facts, persisted in a Redis hash."""

    @staticmethod
    def _key(project_id: str) -> str:
        return f"project:{project_id}:facts"

    async def set_fact(self, project_id: str, field: str, value: Any) -> bool:
        """Store a single JSON-serializable fact under ``field``."""
        client = get_redis()
        if client is None:
            return False
        try:
            await client.hset(self._key(project_id), field, json.dumps(value))
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("project_set_fact_failed", project_id=project_id, error=str(exc))
            return False

    async def get_fact(self, project_id: str, field: str) -> Any | None:
        """Return a stored fact, or ``None`` if absent/unavailable."""
        client = get_redis()
        if client is None:
            return None
        try:
            raw = await client.hget(self._key(project_id), field)
            return json.loads(raw) if raw is not None else None
        except Exception as exc:  # noqa: BLE001
            logger.warning("project_get_fact_failed", project_id=project_id, error=str(exc))
            return None

    async def all_facts(self, project_id: str) -> dict[str, Any]:
        """Return every stored fact for a project as a decoded dict."""
        client = get_redis()
        if client is None:
            return {}
        try:
            raw = await client.hgetall(self._key(project_id))
            result: dict[str, Any] = {}
            for field, value in (raw or {}).items():
                try:
                    result[field] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[field] = value
            return result
        except Exception as exc:  # noqa: BLE001
            logger.warning("project_all_facts_failed", project_id=project_id, error=str(exc))
            return {}

    async def save_schema_summary(self, project_id: str, summary: Any) -> bool:
        """Convenience: store the introspected schema summary."""
        return await self.set_fact(project_id, "schema_summary", summary)

    async def get_schema_summary(self, project_id: str) -> Any | None:
        """Convenience: retrieve the stored schema summary."""
        return await self.get_fact(project_id, "schema_summary")


__all__ = ["ProjectMemory"]
