"""Recommendation agent: derives prioritized, actionable recommendations."""

from __future__ import annotations

import json
from typing import Any

from app.agents.base import BaseAgent
from app.prompts.recommendation import RECOMMENDATION_SYSTEM_PROMPT
from app.schemas.analysis import RecommendationSet


class RecommendationAgent(BaseAgent[RecommendationSet]):
    """Produce a prioritized :class:`RecommendationSet` from the insights."""

    name = "recommendation"
    output_schema = RecommendationSet

    def system_prompt(self, state: dict[str, Any]) -> str:
        return RECOMMENDATION_SYSTEM_PROMPT

    def user_prompt(self, state: dict[str, Any]) -> str:
        question = state.get("question", "")
        intent = state.get("intent", {})
        insights = state.get("insights", {})
        statistics = state.get("statistics", {})
        parts = [f"User question:\n{question}"]
        if intent:
            parts.append("Detected intent:\n" + json.dumps(intent, default=str))
        if insights:
            parts.append("Insights:\n" + json.dumps(insights, default=str)[:5000])
        if statistics:
            parts.append(
                "Supporting statistics:\n" + json.dumps(statistics, default=str)[:4000]
            )
        parts.append(
            "Return a RecommendationSet ordered highest to lowest priority."
        )
        return "\n\n".join(parts)
