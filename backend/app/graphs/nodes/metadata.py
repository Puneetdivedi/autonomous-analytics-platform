"""Metadata node — inspects/narrows the schema to the relevant tables.

If the state has no schema yet (e.g. it was not pre-loaded by the service), the
node introspects the data source via its adapter first.
"""

from __future__ import annotations

from typing import Any

import anyio

from app.agents.registry import get_agent
from app.graphs.nodes._helpers import event, run_node


def _introspect(datasource: dict[str, Any]) -> dict[str, Any]:
    from app.models.enums import DataSourceType
    from app.services.data_sources.factory import get_adapter

    adapter = get_adapter(
        DataSourceType(datasource["type"]),
        connection_uri=datasource.get("connection_uri"),
        file_path=datasource.get("file_path"),
    )
    try:
        tables = adapter.introspect_schema()
    finally:
        adapter.close()
    return {t.table: [c.model_dump() for c in t.columns] for t in tables}


async def metadata(state: dict[str, Any]) -> dict[str, Any]:
    async def body(s: dict[str, Any]) -> dict[str, Any]:
        schema = s.get("schema") or {}
        datasource = (s.get("memory") or {}).get("datasource")
        if not schema and datasource:
            schema = await anyio.to_thread.run_sync(_introspect, datasource)

        relevant = await get_agent("metadata").run({**s, "schema": schema})
        return {
            "schema": schema,
            "relevant_tables": relevant.relevant_tables,
            "events": [event("artifact", "metadata", relevant_tables=relevant.relevant_tables)],
        }

    return await run_node("metadata", "metadata", state, body)
