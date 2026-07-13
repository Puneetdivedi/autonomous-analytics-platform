"""Planner node — produces an ordered execution plan."""

from __future__ import annotations

from typing import Any

from app.agents.registry import get_agent
from app.graphs.nodes._helpers import event, run_node


async def planner(state: dict[str, Any]) -> dict[str, Any]:
    async def body(s: dict[str, Any]) -> dict[str, Any]:
        plan = await get_agent("planner").run(s)
        steps = [step.model_dump() for step in plan.steps]
        return {
            "plan": steps,
            "events": [event("artifact", "planner", plan=steps, rationale=plan.rationale)],
        }

    return await run_node("planner", "planner", state, body)
