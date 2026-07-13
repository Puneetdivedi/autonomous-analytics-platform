"""Intent detection node — classifies the user's question."""

from __future__ import annotations

from typing import Any

from app.agents.registry import get_agent
from app.graphs.nodes._helpers import event, run_node


async def intent_detection(state: dict[str, Any]) -> dict[str, Any]:
    async def body(s: dict[str, Any]) -> dict[str, Any]:
        intent = await get_agent("intent").run(s)
        payload = intent.model_dump()
        return {
            "intent": payload,
            "events": [event("artifact", "intent_detection", intent=payload)],
        }

    return await run_node("intent_detection", "intent", state, body)
