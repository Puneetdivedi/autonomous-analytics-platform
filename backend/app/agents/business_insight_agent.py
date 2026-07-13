"""Business-insight agent: synthesizes data and stats into an executive narrative."""

from __future__ import annotations

import json
from typing import Any

from app.agents.base import BaseAgent
from app.prompts.business_insight import BUSINESS_INSIGHT_SYSTEM_PROMPT
from app.schemas.analysis import Insights


class BusinessInsightAgent(BaseAgent[Insights]):
    """Produce an :class:`Insights` narrative from data, statistics, and charts."""

    name = "business_insight"
    output_schema = Insights

    def system_prompt(self, state: dict[str, Any]) -> str:
        return BUSINESS_INSIGHT_SYSTEM_PROMPT

    def user_prompt(self, state: dict[str, Any]) -> str:
        question = state.get("question", "")
        intent = state.get("intent", {})
        columns = state.get("result_columns", [])
        rows = state.get("result_rows", [])
        statistics = state.get("statistics", {})
        charts = state.get("charts", [])
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
            parts.append("Statistics:\n" + json.dumps(statistics, default=str)[:6000])
        if charts:
            # Include only chart metadata, not embedded image payloads.
            meta = [{k: c.get(k) for k in ("type", "title", "x", "y") if k in c} for c in charts]
            parts.append("Charts prepared:\n" + json.dumps(meta, default=str)[:2000])
        parts.append("Return the structured Insights.")
        return "\n\n".join(parts)
