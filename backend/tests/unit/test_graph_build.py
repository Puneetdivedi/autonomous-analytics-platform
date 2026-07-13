"""Unit test: the supervisor graph builds and compiles with all nodes."""

from __future__ import annotations

import pytest

from app.graphs.builder import build_graph, get_compiled_graph
from app.graphs.state import initial_state

pytestmark = pytest.mark.unit

EXPECTED_NODES = {
    "intent_detection",
    "planner",
    "metadata",
    "sql_generator",
    "sql_validator",
    "execution",
    "statistical_analysis",
    "visualization",
    "insight",
    "recommendation",
    "reflection",
    "report_generator",
    "langfuse_logger",
}


def test_graph_contains_all_nodes() -> None:
    compiled = get_compiled_graph()
    nodes = set(compiled.get_graph().nodes.keys())
    assert EXPECTED_NODES.issubset(nodes)


def test_build_graph_is_fresh_instance() -> None:
    assert build_graph() is not build_graph()


def test_initial_state_defaults() -> None:
    state = initial_state(
        question="Why did revenue drop?",
        trace_id="t1",
        project_id="p1",
        chat_id="c1",
        message_id="m1",
        user_id="u1",
        datasource_id=None,
    )
    assert state["question"] == "Why did revenue drop?"
    assert state["retry_count"] == 0
    assert state["completed_tasks"] == []
