"""Visualization node.

The Chart Generator agent decides chart types and axes; we then attach
frontend-ready data (via ``build_chart_data``) and a server-rendered PNG (via
``render_chart``) for report embedding.
"""

from __future__ import annotations

from typing import Any

import anyio

from app.agents.registry import get_agent
from app.core.logging import get_logger
from app.graphs.nodes._helpers import event, run_node
from app.schemas.analysis import ChartSpec

logger = get_logger(__name__)


def _finalize_chart(spec: ChartSpec, rows: list[dict[str, Any]]) -> dict[str, Any]:
    from app.tools.chart_tool import build_chart_data, render_chart
    from app.tools.pandas_tool import dataframe_from_rows

    if not spec.data and spec.x and spec.y:
        try:
            df = dataframe_from_rows(rows)
            spec.data = build_chart_data(df, spec.x, spec.y)
        except Exception as exc:  # noqa: BLE001
            logger.warning("chart_data_failed", error=str(exc))
    try:
        spec.image_b64 = render_chart(spec)
    except Exception as exc:  # noqa: BLE001
        logger.warning("chart_render_failed", error=str(exc))
    return spec.model_dump()


async def visualization(state: dict[str, Any]) -> dict[str, Any]:
    async def body(s: dict[str, Any]) -> dict[str, Any]:
        rows = s.get("result_rows") or []
        if not rows:
            return {"charts": [], "events": [event("artifact", "charts", charts=[])]}

        plan = await get_agent("chart_generator").run(s)
        charts = [
            await anyio.to_thread.run_sync(_finalize_chart, spec, rows) for spec in plan.charts
        ]
        # Strip base64 from the streamed event to keep the SSE payload small.
        light = [{k: v for k, v in c.items() if k != "image_b64"} for c in charts]
        return {"charts": charts, "events": [event("artifact", "charts", charts=light)]}

    return await run_node("visualization", "chart_generator", state, body)
