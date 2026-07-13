"""Supervisor graph construction.

Wires the specialized nodes into a LangGraph ``StateGraph`` with the two
conditional retry loops described in ``docs/ARCHITECTURE.md``:

* ``sql_validator`` → back to ``sql_generator`` while SQL is invalid and budget
  remains; otherwise forward.
* ``reflection`` → back to ``planner`` when the answer needs work and budget
  remains; otherwise to ``report_generator``.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.graphs.nodes.execution import execution
from app.graphs.nodes.insight import insight
from app.graphs.nodes.intent_detection import intent_detection
from app.graphs.nodes.langfuse_logger import langfuse_logger
from app.graphs.nodes.metadata import metadata
from app.graphs.nodes.planner import planner
from app.graphs.nodes.recommendation import recommendation
from app.graphs.nodes.reflection import reflection
from app.graphs.nodes.report_generator import report_generator
from app.graphs.nodes.sql_generator import sql_generator
from app.graphs.nodes.sql_validator import sql_validator
from app.graphs.nodes.statistical_analysis import statistical_analysis
from app.graphs.nodes.visualization import visualization
from app.graphs.state import AnalyticsState

_VALID_RETRY_TARGETS = {"planner", "metadata", "sql_generator"}


def _after_validation(state: dict[str, Any]) -> str:
    if state.get("sql_valid"):
        return "execution"
    if int(state.get("retry_count", 0)) < int(state.get("max_retries", 2)):
        return "sql_generator"
    # Out of retries: skip execution and let the narrative explain the failure.
    return "insight"


def _after_reflection(state: dict[str, Any]) -> str:
    reflection_data = state.get("reflection") or {}
    if reflection_data.get("needs_retry"):
        target = reflection_data.get("retry_target", "planner")
        return target if target in _VALID_RETRY_TARGETS else "planner"
    return "report_generator"


def build_graph() -> StateGraph:
    """Construct (uncompiled) the supervisor ``StateGraph``."""
    graph = StateGraph(AnalyticsState)

    graph.add_node("intent_detection", intent_detection)
    graph.add_node("planner", planner)
    graph.add_node("metadata", metadata)
    graph.add_node("sql_generator", sql_generator)
    graph.add_node("sql_validator", sql_validator)
    graph.add_node("execution", execution)
    graph.add_node("statistical_analysis", statistical_analysis)
    graph.add_node("visualization", visualization)
    graph.add_node("insight", insight)
    graph.add_node("recommendation", recommendation)
    graph.add_node("reflection", reflection)
    graph.add_node("report_generator", report_generator)
    graph.add_node("langfuse_logger", langfuse_logger)

    graph.add_edge(START, "intent_detection")
    graph.add_edge("intent_detection", "planner")
    graph.add_edge("planner", "metadata")
    graph.add_edge("metadata", "sql_generator")
    graph.add_edge("sql_generator", "sql_validator")

    graph.add_conditional_edges(
        "sql_validator",
        _after_validation,
        {"execution": "execution", "sql_generator": "sql_generator", "insight": "insight"},
    )

    graph.add_edge("execution", "statistical_analysis")
    graph.add_edge("statistical_analysis", "visualization")
    graph.add_edge("visualization", "insight")
    graph.add_edge("insight", "recommendation")
    graph.add_edge("recommendation", "reflection")

    graph.add_conditional_edges(
        "reflection",
        _after_reflection,
        {
            "planner": "planner",
            "metadata": "metadata",
            "sql_generator": "sql_generator",
            "report_generator": "report_generator",
        },
    )

    graph.add_edge("report_generator", "langfuse_logger")
    graph.add_edge("langfuse_logger", END)

    return graph


@lru_cache
def get_compiled_graph() -> Any:
    """Return the compiled, cached supervisor graph."""
    return build_graph().compile()
