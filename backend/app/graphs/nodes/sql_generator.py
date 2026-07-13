"""SQL generator node — writes SQL for the question against the schema."""

from __future__ import annotations

from typing import Any

from app.agents.registry import get_agent
from app.graphs.nodes._helpers import event, run_node


async def sql_generator(state: dict[str, Any]) -> dict[str, Any]:
    async def body(s: dict[str, Any]) -> dict[str, Any]:
        generated = await get_agent("sql_generator").run(s)
        return {
            "sql_query": generated.sql,
            "sql_dialect": generated.dialect,
            "events": [
                event(
                    "artifact",
                    "sql_generator",
                    sql=generated.sql,
                    explanation=generated.explanation,
                )
            ],
        }

    return await run_node("sql_generator", "sql_generator", state, body)
