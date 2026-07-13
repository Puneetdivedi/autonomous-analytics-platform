"""LangFuse logger node — final node that flushes the trace and emits `done`."""

from __future__ import annotations

from typing import Any

from app.graphs.nodes._helpers import event, run_node
from app.observability import get_langfuse


async def langfuse_logger(state: dict[str, Any]) -> dict[str, Any]:
    async def body(s: dict[str, Any]) -> dict[str, Any]:
        client = get_langfuse()
        if client is not None:
            try:
                client.flush()
            except Exception:  # noqa: BLE001
                pass
        return {
            "events": [
                event(
                    "done",
                    "langfuse_logger",
                    trace_id=s.get("trace_id"),
                    completed_tasks=s.get("completed_tasks", []),
                    errors=s.get("errors", []),
                )
            ]
        }

    return await run_node("langfuse_logger", "langfuse_logger", state, body)
