"""Memory tool — thin façade over :mod:`app.memory`.

Provides small ``remember`` / ``recall`` helpers for agents and graph nodes.
The heavy ``app.memory`` imports are deferred to call time to avoid import
cycles and so the module loads even when Redis/Qdrant are unavailable.
"""

from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from app.core.logging import get_logger

logger = get_logger(__name__)


async def remember(namespace: str, key: str, value: str, *, metadata: dict[str, Any] | None = None) -> bool:
    """Persist a memory item for later semantic recall.

    Stores ``value`` under ``namespace`` in the long-term (vector) store. The
    ``key`` is attached as metadata for traceability. Returns ``True`` on
    success and ``False`` if the backing store is unavailable (never raises).
    """
    try:
        from app.memory.long_term import LongTermMemory

        store = LongTermMemory()
        meta = {"key": key, **(metadata or {})}
        return await store.add(namespace, value, meta)
    except Exception as exc:  # noqa: BLE001
        logger.warning("remember_failed", namespace=namespace, error=str(exc))
        return False


async def recall(namespace: str, query: str, k: int = 5) -> list[dict[str, Any]]:
    """Recall up to ``k`` memory items semantically similar to ``query``.

    Returns a list of ``{text, metadata, score}`` dicts, or an empty list if
    the backing store is unavailable (never raises).
    """
    try:
        from app.memory.long_term import LongTermMemory

        store = LongTermMemory()
        return await store.search(namespace, query, k)
    except Exception as exc:  # noqa: BLE001
        logger.warning("recall_failed", namespace=namespace, error=str(exc))
        return []


async def _impl(namespace: str, query: str, k: int = 5) -> list[dict[str, Any]]:
    """Recall memory items relevant to a query from a namespace."""
    return await recall(namespace, query, k)


memory_tool = tool(_impl)

__all__ = ["memory_tool", "remember", "recall"]
