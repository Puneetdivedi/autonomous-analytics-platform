"""Statistical analysis node.

The numeric heavy-lifting is deterministic (``statistics_tool.full_report``); the
Python Analyst agent then interprets/augments the computed report so downstream
narrative agents work from trustworthy numbers.
"""

from __future__ import annotations

from typing import Any

import anyio

from app.agents.registry import get_agent
from app.graphs.nodes._helpers import event, run_node


def _compute(rows: list[dict[str, Any]]) -> dict[str, Any]:
    from app.tools.pandas_tool import dataframe_from_rows
    from app.tools.statistics_tool import full_report

    df = dataframe_from_rows(rows)
    return full_report(df).model_dump()


async def statistical_analysis(state: dict[str, Any]) -> dict[str, Any]:
    async def body(s: dict[str, Any]) -> dict[str, Any]:
        rows = s.get("result_rows") or []
        if not rows:
            return {"statistics": {}, "events": [event("artifact", "statistics", empty=True)]}

        computed = await anyio.to_thread.run_sync(_compute, rows)
        # Let the analyst agent interpret; fall back to raw computed report on failure.
        try:
            interpreted = await get_agent("python_analyst").run({**s, "statistics": computed})
            stats = interpreted.model_dump()
        except Exception:  # noqa: BLE001
            stats = computed
        return {
            "statistics": stats,
            "events": [event("artifact", "statistics", statistics=stats)],
        }

    return await run_node("statistical_analysis", "python_analyst", state, body)
