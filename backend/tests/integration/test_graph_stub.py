"""End-to-end graph test using the stub LLM — runs the whole supervisor with no key."""

from __future__ import annotations

import pytest

from app.core.config import settings
from app.graphs.runner import run_graph
from app.graphs.state import initial_state

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

CSV = (
    "region,month,revenue,units\n"
    "NA,2025-04,200000,5600\n"
    "NA,2025-05,156000,4300\n"
    "EU,2025-04,70000,2300\n"
    "EU,2025-05,74000,2450\n"
)


async def test_full_graph_runs_with_stub(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "llm_provider", "stub")
    monkeypatch.setattr(settings, "report_dir", str(tmp_path))

    csv_path = tmp_path / "sales.csv"
    csv_path.write_text(CSV, encoding="utf-8")

    state = initial_state(
        question="Why did revenue decrease in North America last month?",
        trace_id="t-stub",
        project_id="p1",
        chat_id="c1",
        message_id="m1",
        user_id="u1",
        datasource_id="d1",
        memory={"datasource": {"type": "csv", "file_path": str(csv_path)}},
    )

    final = {}
    node_events = []
    async for evt in run_graph(state):
        if evt.get("type") == "__final__":
            final = evt["state"]
        elif evt.get("type") == "node_end":
            node_events.append(evt["node"])

    # The full pipeline completed without errors.
    assert final.get("errors") == [] or not final.get("errors")
    # Core nodes all ran.
    for node in ("intent_detection", "sql_generator", "execution", "insight", "report_generator"):
        assert node in node_events, f"{node} did not run"
    # Real data flowed through: SQL executed and produced rows.
    assert final["row_count"] > 0
    assert final["sql_query"].upper().startswith("SELECT")
    # Narrative + artifacts were produced.
    assert final["insights"]["executive_summary"]
    assert final["recommendations"]
    assert final["report"]["file_path"]
