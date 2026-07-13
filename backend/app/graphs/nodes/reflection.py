"""Reflection node — self-critiques the answer and decides whether to retry."""

from __future__ import annotations

from typing import Any

from app.agents.registry import get_agent
from app.graphs.nodes._helpers import event, run_node


async def reflection(state: dict[str, Any]) -> dict[str, Any]:
    async def body(s: dict[str, Any]) -> dict[str, Any]:
        result = await get_agent("reflection").run(s)
        # Only honor a retry request while retry budget remains.
        budget_left = int(s.get("retry_count", 0)) < int(s.get("max_retries", 2))
        needs_retry = bool(result.needs_retry and budget_left)
        payload = {
            "quality_score": result.quality_score,
            "needs_retry": needs_retry,
            "retry_target": result.retry_target or "planner",
            "feedback": result.feedback,
        }
        update: dict[str, Any] = {
            "reflection": payload,
            "events": [event("artifact", "reflection", **payload)],
        }
        if needs_retry:
            update["retry_count"] = int(s.get("retry_count", 0)) + 1
        return update

    return await run_node("reflection", "reflection", state, body)
