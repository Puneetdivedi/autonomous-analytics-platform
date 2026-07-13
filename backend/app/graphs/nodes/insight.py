"""Insight node — executive summary, key findings, root-cause, risks, opportunities."""

from __future__ import annotations

from typing import Any

from app.agents.registry import get_agent
from app.graphs.nodes._helpers import event, run_node


async def insight(state: dict[str, Any]) -> dict[str, Any]:
    async def body(s: dict[str, Any]) -> dict[str, Any]:
        insights = await get_agent("business_insight").run(s)
        payload = insights.model_dump()
        return {
            "insights": payload,
            "events": [event("artifact", "insight", insights=payload)],
        }

    return await run_node("insight", "business_insight", state, body)
