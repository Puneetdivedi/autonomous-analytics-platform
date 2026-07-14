"""Metadata node — inspects the schema and enriches it with real column values.

Beyond table/column discovery, this node fetches the **distinct values** of each
low-cardinality categorical column in the relevant tables and attaches them to
the schema. That lets the SQL generator map a user's wording to the values that
actually exist in the data (e.g. "North America" -> "NA") instead of guessing.
"""

from __future__ import annotations

from typing import Any

import anyio

from app.agents.registry import get_agent
from app.core.logging import get_logger
from app.graphs.nodes._helpers import event, run_node

logger = get_logger(__name__)

_MAX_TABLES = 3
_MAX_DISTINCT = 25
_NUMERIC_HINTS = ("int", "float", "num", "real", "double", "dec", "serial", "bool", "date", "time")


def _adapter(datasource: dict[str, Any]):
    from app.models.enums import DataSourceType
    from app.services.data_sources.factory import get_adapter

    return get_adapter(
        DataSourceType(datasource["type"]),
        connection_uri=datasource.get("connection_uri"),
        file_path=datasource.get("file_path"),
    )


def _introspect(datasource: dict[str, Any]) -> dict[str, Any]:
    adapter = _adapter(datasource)
    try:
        tables = adapter.introspect_schema()
    finally:
        adapter.close()
    return {t.table: [c.model_dump() for c in t.columns] for t in tables}


def _normalize(schema: Any) -> dict[str, list[dict[str, Any]]]:
    """Coerce either schema shape into ``{table: [ {name, type, nullable}, ... ]}``."""
    out: dict[str, list[dict[str, Any]]] = {}
    if isinstance(schema, dict) and "tables" in schema:
        for t in schema["tables"]:
            out[t.get("table")] = [dict(c) for c in t.get("columns", [])]
    elif isinstance(schema, dict):
        for name, cols in schema.items():
            if isinstance(cols, list):
                out[name] = [dict(c) for c in cols]
    return out


def _is_categorical(type_str: str) -> bool:
    return not any(h in (type_str or "").lower() for h in _NUMERIC_HINTS)


def _augment_with_values(
    datasource: dict[str, Any],
    schema: dict[str, list[dict[str, Any]]],
    relevant: list[str],
) -> dict[str, list[dict[str, Any]]]:
    """Attach ``sample_values`` to low-cardinality categorical columns."""
    targets = [t for t in relevant if t in schema] or list(schema)[:_MAX_TABLES]
    adapter = _adapter(datasource)
    try:
        for table in targets[:_MAX_TABLES]:
            for col in schema.get(table, []):
                if not _is_categorical(col.get("type", "")):
                    continue
                name = col.get("name")
                try:
                    res = adapter.run_query(
                        f'SELECT DISTINCT "{name}" FROM "{table}" LIMIT {_MAX_DISTINCT + 1}'
                    )
                    values = [r.get(name) for r in res.get("rows", []) if r.get(name) is not None]
                    if 0 < len(values) <= _MAX_DISTINCT:
                        col["sample_values"] = values
                except Exception as exc:  # noqa: BLE001
                    logger.debug("distinct_values_failed", table=table, column=name, error=str(exc))
    finally:
        adapter.close()
    return schema


async def metadata(state: dict[str, Any]) -> dict[str, Any]:
    async def body(s: dict[str, Any]) -> dict[str, Any]:
        schema = s.get("schema") or {}
        datasource = (s.get("memory") or {}).get("datasource")
        if not schema and datasource:
            schema = await anyio.to_thread.run_sync(_introspect, datasource)

        relevant = await get_agent("metadata").run({**s, "schema": schema})

        normalized = _normalize(schema)
        if datasource and normalized:
            normalized = await anyio.to_thread.run_sync(
                _augment_with_values, datasource, normalized, relevant.relevant_tables
            )

        return {
            "schema": normalized,
            "relevant_tables": relevant.relevant_tables,
            "events": [
                event("artifact", "metadata", relevant_tables=relevant.relevant_tables)
            ],
        }

    return await run_node("metadata", "metadata", state, body)
