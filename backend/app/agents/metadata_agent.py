"""Metadata agent: schema linking — selects the tables relevant to a question."""

from __future__ import annotations

import json
from typing import Any

from app.agents.base import BaseAgent
from app.prompts.metadata import METADATA_SYSTEM_PROMPT
from app.schemas.analysis import RelevantSchema


class MetadataAgent(BaseAgent[RelevantSchema]):
    """Select the minimal :class:`RelevantSchema` needed to answer the question."""

    name = "metadata"
    output_schema = RelevantSchema

    def system_prompt(self, state: dict[str, Any]) -> str:
        return METADATA_SYSTEM_PROMPT

    def user_prompt(self, state: dict[str, Any]) -> str:
        question = state.get("question", "")
        intent = state.get("intent", {})
        schema = state.get("schema", {})
        parts = [f"User question:\n{question}"]
        if intent:
            parts.append("Detected intent:\n" + json.dumps(intent, default=str))
        parts.append(
            "Full datasource schema (tables -> columns):\n"
            + json.dumps(schema, default=str)[:8000]
        )
        parts.append("Return the RelevantSchema (tables that must be used).")
        return "\n\n".join(parts)
