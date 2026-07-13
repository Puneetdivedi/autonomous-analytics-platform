"""Execution node — runs the validated SQL against the data source adapter."""

from __future__ import annotations

from typing import Any

import anyio

from app.core.config import settings
from app.core.exceptions import SQLExecutionError
from app.graphs.nodes._helpers import event, run_node


def _run_query(datasource: dict[str, Any], sql: str) -> dict[str, Any]:
    from app.models.enums import DataSourceType
    from app.services.data_sources.factory import get_adapter

    adapter = get_adapter(
        DataSourceType(datasource["type"]),
        connection_uri=datasource.get("connection_uri"),
        file_path=datasource.get("file_path"),
    )
    try:
        return adapter.run_query(sql)
    finally:
        adapter.close()


async def execution(state: dict[str, Any]) -> dict[str, Any]:
    async def body(s: dict[str, Any]) -> dict[str, Any]:
        datasource = (s.get("memory") or {}).get("datasource")
        if not datasource:
            raise SQLExecutionError("No data source is attached to this request.")
        sql = s.get("sql_query", "")
        result = await anyio.to_thread.run_sync(_run_query, datasource, sql)
        rows = result["rows"][: settings.max_sql_rows]
        return {
            "result_rows": rows,
            "result_columns": result["columns"],
            "row_count": result["row_count"],
            "events": [
                event(
                    "artifact",
                    "execution",
                    row_count=result["row_count"],
                    columns=result["columns"],
                    preview=rows[:20],
                )
            ],
        }

    return await run_node("execution", "execution", state, body)
