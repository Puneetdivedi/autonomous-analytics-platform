"""SQL validator node — combines a deterministic safety check with an LLM review.

Sets ``sql_valid``. When invalid, increments ``retry_count`` (the builder's
conditional edge routes back to the generator while budget remains) and applies
a corrected query if the agent supplied one.
"""

from __future__ import annotations

from typing import Any

from app.agents.registry import get_agent
from app.graphs.nodes._helpers import event, run_node
from app.tools.sql_tool import validate_sql


async def sql_validator(state: dict[str, Any]) -> dict[str, Any]:
    async def body(s: dict[str, Any]) -> dict[str, Any]:
        sql = s.get("sql_query", "")
        deterministic_ok = True
        notes = ""
        try:
            validate_sql(sql)  # raises on non-SELECT / multi-statement / unsafe
        except Exception as exc:  # noqa: BLE001
            deterministic_ok = False
            notes = str(exc)

        review = await get_agent("sql_validator").run(s)
        is_valid = deterministic_ok and review.is_valid and review.is_safe
        update: dict[str, Any] = {
            "sql_valid": is_valid,
            "sql_validation_notes": notes or "; ".join(review.issues),
            "events": [
                event(
                    "artifact",
                    "sql_validator",
                    is_valid=is_valid,
                    issues=review.issues,
                )
            ],
        }
        if not is_valid:
            update["retry_count"] = int(s.get("retry_count", 0)) + 1
            if review.corrected_sql:
                update["sql_query"] = review.corrected_sql
        return update

    return await run_node("sql_validator", "sql_validator", state, body)
