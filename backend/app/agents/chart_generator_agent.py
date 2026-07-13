"""Chart-generation agent: selects chart types and prepares Recharts specs."""

from __future__ import annotations

import json
from typing import Any

from app.agents.base import BaseAgent
from app.prompts.chart_generator import CHART_GENERATOR_SYSTEM_PROMPT
from app.schemas.analysis import ChartPlan


class ChartGeneratorAgent(BaseAgent[ChartPlan]):
    """Decide visualizations and return a :class:`ChartPlan` from the result set."""

    name = "chart_generator"
    output_schema = ChartPlan

    def system_prompt(self, state: dict[str, Any]) -> str:
        return CHART_GENERATOR_SYSTEM_PROMPT

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
        if statistics:
            parts.append(
                "Statistics context:\n" + json.dumps(statistics, default=str)[:3000]
            )
        parts.append(
            "Return a ChartPlan with 1-3 focused charts using only these columns."
        )
        return "\n\n".join(parts)
