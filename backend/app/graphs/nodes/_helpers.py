"""Shared helpers for graph nodes: timing, execution records, and events.

Every node wraps its body in :func:`run_node` which produces the standard
append-only ``executions`` and ``events`` entries and captures errors without
crashing the whole graph (a failed node records the error and returns a partial
update so downstream nodes / reflection can decide what to do).
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from app.core.logging import get_logger
from app.models.enums import AgentStatus

logger = get_logger(__name__)

NodeBody = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


def event(type_: str, node: str, **data: Any) -> dict[str, Any]:
    """Build a StreamEvent-shaped dict for the streaming sink."""
    return {"type": type_, "node": node, "data": data}


def execution_record(
    *,
    node_name: str,
    agent_name: str,
    status: AgentStatus,
    attempt: int = 1,
    latency_ms: float | None = None,
    error: str | None = None,
    output: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an AgentExecution-shaped dict appended to ``state['executions']``."""
    return {
        "node_name": node_name,
        "agent_name": agent_name,
        "status": status.value,
        "attempt": attempt,
        "latency_ms": latency_ms,
        "error": error,
        "output_payload": output or {},
    }


async def run_node(
    node_name: str,
    agent_name: str,
    state: dict[str, Any],
    body: NodeBody,
) -> dict[str, Any]:
    """Execute ``body`` with timing, event emission and error capture.

    Returns a partial-state dict that always includes ``executions`` and
    ``events`` append entries, plus whatever ``body`` returned on success.
    """
    log = logger.bind(node=node_name)
    start = time.perf_counter()
    events = [event("node_start", node_name)]

    try:
        update = await body(state)
        latency = (time.perf_counter() - start) * 1000
        log.info("node_ok", latency_ms=round(latency, 1))
        update = update or {}
        # Merge any events the body emitted (e.g. artifact events) before node_end.
        events.extend(update.pop("events", []))
        events.append(event("node_end", node_name, latency_ms=round(latency, 1)))
        update.setdefault("current_task", node_name)
        update["executions"] = [
            execution_record(
                node_name=node_name,
                agent_name=agent_name,
                status=AgentStatus.SUCCESS,
                latency_ms=latency,
                output={k: _truncate(v) for k, v in update.items()},
            )
        ]
        update["events"] = events
        update["completed_tasks"] = [node_name]
        return update
    except Exception as exc:  # noqa: BLE001
        latency = (time.perf_counter() - start) * 1000
        log.error("node_failed", error=str(exc), latency_ms=round(latency, 1))
        return {
            "errors": [{"node": node_name, "error": str(exc)}],
            "events": [*events, event("error", node_name, message=str(exc))],
            "executions": [
                execution_record(
                    node_name=node_name,
                    agent_name=agent_name,
                    status=AgentStatus.FAILED,
                    latency_ms=latency,
                    error=str(exc),
                )
            ],
        }


def _truncate(value: Any, limit: int = 2000) -> Any:
    """Truncate large payloads before storing in execution records."""
    if isinstance(value, str) and len(value) > limit:
        return value[:limit] + "…"
    if isinstance(value, list) and len(value) > 50:
        return value[:50]
    return value
