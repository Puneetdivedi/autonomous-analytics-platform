"""SQL-generation agent: writes a single read-only SELECT for the question."""

from __future__ import annotations

import json
from typing import Any

from app.agents.base import BaseAgent
from app.prompts.sql_generator import SQL_GENERATOR_SYSTEM_PROMPT
from app.schemas.analysis import GeneratedSQL


class SQLGeneratorAgent(BaseAgent[GeneratedSQL]):
    """Generate a :class:`GeneratedSQL` (read-only SELECT) for the question."""

    name = "sql_generator"
    output_schema = GeneratedSQL

    def system_prompt(self, state: dict[str, Any]) -> str:
        return SQL_GENERATOR_SYSTEM_PROMPT

    def user_prompt(self, state: dict[str, Any]) -> str:
        question = state.get("question", "")
        intent = state.get("intent", {})
        schema = state.get("schema", {})
        relevant_tables = state.get("relevant_tables", [])
        dialect = state.get("sql_dialect", "postgresql")
        parts = [f"User question:\n{question}", f"Target SQL dialect: {dialect}"]
        if intent:
            parts.append("Detected intent:\n" + json.dumps(intent, default=str))
        if relevant_tables:
            parts.append(
                "Relevant tables to build around:\n" + json.dumps(relevant_tables, default=str)
            )
        parts.append("Schema (tables -> columns):\n" + json.dumps(schema, default=str)[:8000])
        parts.append(
            "IMPORTANT — filter values: some columns include a `sample_values` list of the "
            "ACTUAL distinct values in the data. When writing WHERE clauses you MUST use those "
            "exact values and map the user's wording to the closest one (e.g. the user says "
            "'North America' but the column only contains 'NA' -> filter on 'NA'). Never invent a "
            "filter value that is not present in the data."
        )
        # Surface reflection feedback so a retry can correct the previous query.
        reflection = state.get("reflection", {})
        if reflection.get("feedback"):
            parts.append("Reviewer feedback to address:\n" + reflection["feedback"])
        parts.append("Return the structured GeneratedSQL. SELECT-only, with a LIMIT.")
        return "\n\n".join(parts)
