"""Reflection agent: evaluates answer quality and decides on retries."""

from __future__ import annotations

import json
from typing import Any

from app.agents.base import BaseAgent
from app.prompts.reflection import REFLECTION_SYSTEM_PROMPT
from app.schemas.analysis import Reflection


class ReflectionAgent(BaseAgent[Reflection]):
    """Assess the end-to-end answer and return a :class:`Reflection` verdict."""

    name = "reflection"
    output_schema = Reflection

    def system_prompt(self, state: dict[str, Any]) -> str:
        return REFLECTION_SYSTEM_PROMPT

    def user_prompt(self, state: dict[str, Any]) -> str:
        question = state.get("question", "")
        intent = state.get("intent", {})
        rows = state.get("result_rows", [])
        sample = rows[:20]
        parts = [f"User question:\n{question}"]
        if intent:
            parts.append("Detected intent:\n" + json.dumps(intent, default=str))
        parts.append(
            "SQL query:\n" + str(state.get("sql_query", ""))
        )
        parts.append(
            f"sql_valid={state.get('sql_valid')} "
            f"row_count={state.get('row_count', len(rows))}"
        )
        if state.get("sql_validation_notes"):
            parts.append("Validation notes:\n" + str(state["sql_validation_notes"]))
        parts.append(
            f"Result rows sample (first {len(sample)}):\n"
            + json.dumps(sample, default=str)[:3000]
        )
        parts.append(
            "Statistics:\n" + json.dumps(state.get("statistics", {}), default=str)[:3000]
        )
        parts.append(
            "Insights:\n" + json.dumps(state.get("insights", {}), default=str)[:3000]
        )
        parts.append(
            "Recommendations:\n"
            + json.dumps(state.get("recommendations", []), default=str)[:3000]
        )
        parts.append(
            f"retry_count={state.get('retry_count', 0)} "
            f"max_retries={state.get('max_retries', 0)}"
        )
        parts.append("Return the structured Reflection.")
        return "\n\n".join(parts)
