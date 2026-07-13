"""Graph runner — executes the supervisor graph and streams events.

Yields StreamEvent-shaped dicts as nodes progress. The final item yielded is a
sentinel ``{"type": "__final__", "state": <full AnalyticsState>}`` so the caller
can both stream to the client and persist the completed state.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger
from app.graphs.builder import get_compiled_graph
from app.graphs.state import AnalyticsState
from app.observability import get_langchain_handler

logger = get_logger(__name__)


async def run_graph(initial_state: AnalyticsState) -> AsyncIterator[dict[str, Any]]:
    """Run the supervisor graph, yielding events then a final-state sentinel."""
    graph = get_compiled_graph()
    handler = get_langchain_handler(
        trace_name="analytics_supervisor",
        user_id=initial_state.get("user_id"),
        session_id=initial_state.get("chat_id"),
        metadata={
            "project_id": initial_state.get("project_id"),
            "message_id": initial_state.get("message_id"),
        },
    )
    config: dict[str, Any] = {"recursion_limit": settings.max_graph_iterations}
    if handler is not None:
        config["callbacks"] = [handler]

    emitted = 0
    final_state: dict[str, Any] = dict(initial_state)

    try:
        async for values in graph.astream(initial_state, config=config, stream_mode="values"):
            final_state = values
            events = values.get("events", [])
            # Emit only newly-appended events since the last step.
            for evt in events[emitted:]:
                yield evt
            emitted = len(events)
    except Exception as exc:  # noqa: BLE001
        logger.error("graph_run_failed", error=str(exc))
        yield {"type": "error", "node": "runner", "data": {"message": str(exc)}}
        final_state.setdefault("errors", []).append({"node": "runner", "error": str(exc)})

    yield {"type": "__final__", "state": final_state}
