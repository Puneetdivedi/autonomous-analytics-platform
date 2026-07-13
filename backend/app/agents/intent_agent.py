"""Intent-detection agent: classifies the user's question into a structured Intent."""

from __future__ import annotations

import json
from typing import Any

from app.agents.base import BaseAgent
from app.prompts.intent import INTENT_SYSTEM_PROMPT
from app.schemas.analysis import Intent


class IntentAgent(BaseAgent[Intent]):
    """Classify a natural-language question into a structured :class:`Intent`."""

    name = "intent"
    output_schema = Intent

    def system_prompt(self, state: dict[str, Any]) -> str:
        return INTENT_SYSTEM_PROMPT

    def user_prompt(self, state: dict[str, Any]) -> str:
        question = state.get("question", "")
        schema = state.get("schema", {})
        memory = state.get("memory", {})
        parts = [f"User question:\n{question}"]
        if schema:
            parts.append(
                "Available schema (tables -> columns):\n" + json.dumps(schema, default=str)[:4000]
            )
        if memory:
            parts.append(
                "Conversation memory (for reference resolution):\n"
                + json.dumps(memory, default=str)[:2000]
            )
        parts.append("Return the structured Intent for this question.")
        return "\n\n".join(parts)
