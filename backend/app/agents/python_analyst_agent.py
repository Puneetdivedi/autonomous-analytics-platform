"""Python analyst agent: interprets pre-computed statistics into a report."""

from __future__ import annotations

import json
from typing import Any

from app.agents.base import BaseAgent
from app.prompts.python_analyst import PYTHON_ANALYST_SYSTEM_PROMPT
from app.schemas.analysis import StatisticsReport


class PythonAnalystAgent(BaseAgent[StatisticsReport]):
    """Interpret ``state['statistics']`` into a curated :class:`StatisticsReport`.

    The heavy numeric work is done by deterministic tools; this agent selects,
    narrates, and never recomputes or fabricates values.
    """

    name = "python_analyst"
    output_schema = StatisticsReport

    def system_prompt(self, state: dict[str, Any]) -> str:
        return PYTHON_ANALYST_SYSTEM_PROMPT

    def user_prompt(self, state: dict[str, Any]) -> str:
        question = state.get("question", "")
        intent = state.get("intent", {})
        columns = state.get("result_columns", [])
        rows = state.get("result_rows", [])
        statistics = state.get("statistics", {})
        sample = rows[:20]
        parts = [f"User question:\n{question}"]
        if intent:
            parts.append("Detected intent:\n" + json.dumps(intent, default=str))
        parts.append("Result columns:\n" + json.dumps(columns, default=str))
        parts.append(
            f"Result rows sample (first {len(sample)} of {len(rows)}):\n"
            + json.dumps(sample, default=str)[:4000]
        )
        parts.append(
            "Pre-computed statistics (authoritative — do not recompute):\n"
            + json.dumps(statistics, default=str)[:8000]
        )
        parts.append("Return the structured StatisticsReport.")
        return "\n\n".join(parts)
