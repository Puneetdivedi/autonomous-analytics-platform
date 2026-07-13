"""SQL-validation agent: gatekeeps generated SQL for correctness and safety."""

from __future__ import annotations

import json
from typing import Any

from app.agents.base import BaseAgent
from app.prompts.sql_validator import SQL_VALIDATOR_SYSTEM_PROMPT
from app.schemas.analysis import SQLValidation


class SQLValidatorAgent(BaseAgent[SQLValidation]):
    """Validate SQL and return a :class:`SQLValidation` verdict."""

    name = "sql_validator"
    output_schema = SQLValidation

    def system_prompt(self, state: dict[str, Any]) -> str:
        return SQL_VALIDATOR_SYSTEM_PROMPT

    def user_prompt(self, state: dict[str, Any]) -> str:
        sql = state.get("sql_query", "")
        dialect = state.get("sql_dialect", "postgresql")
        schema = state.get("schema", {})
        relevant_tables = state.get("relevant_tables", [])
        parts = [
            f"Target SQL dialect: {dialect}",
            f"Candidate SQL to review:\n{sql}",
        ]
        if relevant_tables:
            parts.append("Intended tables:\n" + json.dumps(relevant_tables, default=str))
        parts.append(
            "Schema (tables -> columns) — ground truth:\n" + json.dumps(schema, default=str)[:8000]
        )
        parts.append("Return the SQLValidation verdict. Enforce single read-only SELECT + LIMIT.")
        return "\n\n".join(parts)
