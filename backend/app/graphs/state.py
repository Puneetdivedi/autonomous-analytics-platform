"""LangGraph shared state contract.

Every node reads from and writes to :class:`AnalyticsState`. It is a plain
`TypedDict` (LangGraph merges partial dict updates returned by nodes). Nested
payloads use Pydantic models (see ``app.schemas.analysis``) serialized to dicts
so the state stays JSON-serializable for checkpointing and LangFuse.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class AnalyticsState(TypedDict, total=False):
    """The full state threaded through the supervisor graph."""

    # --- Identity / context ---
    trace_id: str
    project_id: str
    chat_id: str
    message_id: str
    user_id: str
    datasource_id: str | None

    # --- The request ---
    question: str
    intent: dict[str, Any]  # {type, entities, time_range, metrics, confidence}

    # --- Planning ---
    plan: list[dict[str, Any]]  # ordered steps [{step, description, node}]
    current_task: str
    completed_tasks: Annotated[list[str], operator.add]

    # --- Schema / metadata ---
    schema: dict[str, Any]  # {table: [{name, type, nullable}]}
    relevant_tables: list[str]

    # --- SQL ---
    sql_query: str
    sql_valid: bool
    sql_validation_notes: str
    sql_dialect: str

    # --- Execution ---
    result_rows: list[dict[str, Any]]
    result_columns: list[str]
    row_count: int

    # --- Analysis ---
    statistics: dict[str, Any]
    charts: list[dict[str, Any]]  # [{type, title, spec, image_b64}]

    # --- Narrative ---
    insights: dict[str, Any]  # {summary, key_findings, root_cause, risks, opportunities}
    recommendations: list[dict[str, Any]]

    # --- Reflection / control ---
    reflection: dict[str, Any]  # {quality_score, needs_retry, feedback, retry_target}
    retry_count: int
    max_retries: int

    # --- Report ---
    report: dict[str, Any]  # {report_id, format, file_path, title}

    # --- Memory ---
    memory: dict[str, Any]  # {conversation, project, preferences, long_term}

    # --- Observability accumulator (append-only) ---
    executions: Annotated[list[dict[str, Any]], operator.add]
    errors: Annotated[list[dict[str, Any]], operator.add]

    # --- Streaming sink (node -> user) ---
    events: Annotated[list[dict[str, Any]], operator.add]


def initial_state(
    *,
    question: str,
    trace_id: str,
    project_id: str,
    chat_id: str,
    message_id: str,
    user_id: str,
    datasource_id: str | None,
    schema: dict[str, Any] | None = None,
    memory: dict[str, Any] | None = None,
    max_retries: int = 2,
) -> AnalyticsState:
    """Construct a fresh state for a new question."""
    return AnalyticsState(
        trace_id=trace_id,
        project_id=project_id,
        chat_id=chat_id,
        message_id=message_id,
        user_id=user_id,
        datasource_id=datasource_id,
        question=question,
        intent={},
        plan=[],
        current_task="intent_detection",
        completed_tasks=[],
        schema=schema or {},
        relevant_tables=[],
        sql_query="",
        sql_valid=False,
        sql_validation_notes="",
        sql_dialect="postgresql",
        result_rows=[],
        result_columns=[],
        row_count=0,
        statistics={},
        charts=[],
        insights={},
        recommendations=[],
        reflection={},
        retry_count=0,
        max_retries=max_retries,
        report={},
        memory=memory or {},
        executions=[],
        errors=[],
        events=[],
    )
