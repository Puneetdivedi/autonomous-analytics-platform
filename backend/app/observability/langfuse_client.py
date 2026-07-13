"""LangFuse client and LangChain callback handler.

Everything is optional: if LangFuse is disabled or keys are missing, the helpers
return ``None`` and callers degrade gracefully (no tracing, no crashes).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@lru_cache
def get_langfuse() -> Any | None:
    """Return a cached LangFuse client, or ``None`` if disabled/misconfigured."""
    if not settings.langfuse_enabled:
        return None
    if not (settings.langfuse_public_key and settings.langfuse_secret_key):
        logger.info("langfuse_disabled", reason="missing keys")
        return None
    try:
        from langfuse import Langfuse

        return Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("langfuse_init_failed", error=str(exc))
        return None


def get_langchain_handler(
    *,
    trace_name: str,
    user_id: str | None = None,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Any | None:
    """Return a LangChain callback handler that streams traces to LangFuse."""
    if not settings.langfuse_enabled:
        return None
    if not (settings.langfuse_public_key and settings.langfuse_secret_key):
        return None
    try:
        from langfuse.callback import CallbackHandler

        return CallbackHandler(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
            trace_name=trace_name,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata or {},
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("langfuse_handler_failed", error=str(exc))
        return None


def shutdown_langfuse() -> None:
    """Flush pending events on application shutdown."""
    client = get_langfuse()
    if client is not None:
        try:
            client.flush()
        except Exception as exc:  # noqa: BLE001
            logger.warning("langfuse_flush_failed", error=str(exc))
