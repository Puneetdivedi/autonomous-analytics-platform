"""Supervisor agent: the orchestrator that (re)plans the analytics pipeline.

The supervisor owns the overall plan and adapts it as the pipeline runs. It does
not itself route or execute nodes — the LangGraph supervisor graph
(:mod:`app.graphs`) performs the actual routing between nodes. This agent decides
*what should happen next* given the current :class:`~app.graphs.state.AnalyticsState`
(completed tasks, retrieval status, and the latest reflection), returning an
updated :class:`~app.schemas.analysis.Plan` of the remaining steps.
"""

from __future__ import annotations

import json
from typing import Any

from app.agents.base import BaseAgent
from app.prompts.supervisor import SUPERVISOR_SYSTEM_PROMPT
from app.schemas.analysis import Plan


class SupervisorAgent(BaseAgent[Plan]):
    """Coordinator agent that produces/updates the remaining :class:`Plan`."""

    name = "supervisor"
    output_schema = Plan

    def system_prompt(self, state: dict[str, Any]) -> str:
        return SUPERVISOR_SYSTEM_PROMPT

    def user_prompt(self, state: dict[str, Any]) -> str:
        question = state.get("question", "")
        intent = state.get("intent", {})
        parts = [f"User question:\n{question}"]
        if intent:
            parts.append("Detected intent:\n" + json.dumps(intent, default=str))
        parts.append(
            "Current plan:\n" + json.dumps(state.get("plan", []), default=str)[:3000]
        )
        parts.append(
            "Completed tasks:\n"
            + json.dumps(state.get("completed_tasks", []), default=str)
        )
        parts.append(f"Current task: {state.get('current_task', '')}")
        parts.append(
            "Relevant tables:\n"
            + json.dumps(state.get("relevant_tables", []), default=str)
        )
        parts.append(
            f"sql_valid={state.get('sql_valid')} row_count={state.get('row_count', 0)}"
        )
        if state.get("reflection"):
            parts.append(
                "Latest reflection:\n"
                + json.dumps(state["reflection"], default=str)[:2000]
            )
        parts.append(
            f"retry_count={state.get('retry_count', 0)} "
            f"max_retries={state.get('max_retries', 0)}"
        )
        if state.get("errors"):
            parts.append(
                "Recent errors:\n" + json.dumps(state["errors"], default=str)[:2000]
            )
        parts.append("Return the updated Plan of remaining steps.")
        return "\n\n".join(parts)
