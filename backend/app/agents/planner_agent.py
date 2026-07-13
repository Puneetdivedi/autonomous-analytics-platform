"""Planning agent: designs the ordered pipeline of steps to answer a question."""

from __future__ import annotations

import json
from typing import Any

from app.agents.base import BaseAgent
from app.prompts.planner import PLANNER_SYSTEM_PROMPT
from app.schemas.analysis import Plan


class PlannerAgent(BaseAgent[Plan]):
    """Produce an ordered :class:`Plan` of pipeline steps for the question."""

    name = "planner"
    output_schema = Plan

    def system_prompt(self, state: dict[str, Any]) -> str:
        return PLANNER_SYSTEM_PROMPT

    def user_prompt(self, state: dict[str, Any]) -> str:
        question = state.get("question", "")
        intent = state.get("intent", {})
        schema = state.get("schema", {})
        memory = state.get("memory", {})
        parts = [f"User question:\n{question}"]
        if intent:
            parts.append("Detected intent:\n" + json.dumps(intent, default=str))
        if schema:
            parts.append(
                "Available schema (tables -> columns):\n" + json.dumps(schema, default=str)[:4000]
            )
        if memory:
            parts.append("Conversation memory:\n" + json.dumps(memory, default=str)[:2000])
        parts.append("Return the structured Plan.")
        return "\n\n".join(parts)
