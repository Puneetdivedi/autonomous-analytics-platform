"""Recommendation node — actionable business recommendations."""

from __future__ import annotations

from typing import Any

from app.agents.registry import get_agent
from app.graphs.nodes._helpers import event, run_node


async def recommendation(state: dict[str, Any]) -> dict[str, Any]:
    async def body(s: dict[str, Any]) -> dict[str, Any]:
        result = await get_agent("recommendation").run(s)
        recs = [r.model_dump() for r in result.recommendations]
        return {
            "recommendations": recs,
            "events": [event("artifact", "recommendation", recommendations=recs)],
        }

    return await run_node("recommendation", "recommendation", state, body)
