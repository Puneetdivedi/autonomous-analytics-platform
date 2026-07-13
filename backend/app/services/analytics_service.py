"""Analytics service — runs the supervisor graph for a question and persists results.

This is the bridge between the API/chat layer and the LangGraph supervisor. It:
1. resolves the data source into an adapter-ready context,
2. builds the initial :class:`AnalyticsState`,
3. streams graph events (for SSE),
4. on completion persists AgentExecutions, the assistant message artifacts, and
   any generated report.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import Any

from app.core.logging import get_logger
from app.database.session import AsyncSessionLocal
from app.graphs.runner import run_graph
from app.graphs.state import initial_state
from app.models.enums import ReportFormat
from app.repositories.agent_execution_repo import AgentExecutionRepository
from app.repositories.datasource_repo import DataSourceRepository
from app.repositories.message_repo import MessageRepository
from app.repositories.report_repo import ReportRepository

logger = get_logger(__name__)


def _synthesize_content(state: dict[str, Any]) -> str:
    """Compose a human-readable markdown answer from the final state."""
    insights = state.get("insights") or {}
    parts: list[str] = []
    if insights.get("executive_summary"):
        parts.append(insights["executive_summary"])
    if insights.get("key_findings"):
        parts.append("\n**Key findings**\n" + "\n".join(f"- {f}" for f in insights["key_findings"]))
    if insights.get("root_cause"):
        parts.append(f"\n**Root cause**\n{insights['root_cause']}")
    recs = state.get("recommendations") or []
    if recs:
        parts.append(
            "\n**Recommendations**\n"
            + "\n".join(f"- **{r.get('title')}** — {r.get('detail')}" for r in recs)
        )
    if not parts and state.get("errors"):
        return "I wasn't able to complete this analysis. " + "; ".join(
            e.get("error", "") for e in state["errors"]
        )
    return "\n".join(parts) or "Analysis complete."


def _artifacts(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "sql": state.get("sql_query"),
        "charts": state.get("charts", []),
        "statistics": state.get("statistics", {}),
        "insights": state.get("insights", {}),
        "recommendations": state.get("recommendations", []),
        "report": state.get("report", {}),
        "row_count": state.get("row_count", 0),
        "columns": state.get("result_columns", []),
        "errors": state.get("errors", []),
    }


class AnalyticsService:
    """Runs the analytics graph and persists its output."""

    async def _resolve_datasource(self, datasource_id: str | None) -> tuple[dict | None, dict]:
        """Return (datasource context, cached schema) for the given id."""
        if not datasource_id:
            return None, {}
        async with AsyncSessionLocal() as session:
            ds = await DataSourceRepository(session).get(datasource_id)
            if ds is None:
                return None, {}
            context = {
                "type": ds.type.value,
                "connection_uri": ds.connection_uri,
                "file_path": ds.file_path,
            }
            return context, (ds.schema_cache or {})

    async def stream(
        self,
        *,
        question: str,
        project_id: str,
        chat_id: str,
        message_id: str,
        user_id: str,
        datasource_id: str | None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Run the graph, yielding SSE events; persists results at the end."""
        trace_id = str(uuid.uuid4())
        datasource, schema = await self._resolve_datasource(datasource_id)

        state = initial_state(
            question=question,
            trace_id=trace_id,
            project_id=project_id,
            chat_id=chat_id,
            message_id=message_id,
            user_id=user_id,
            datasource_id=datasource_id,
            schema=schema,
            memory={"datasource": datasource} if datasource else {},
        )

        final_state: dict[str, Any] = dict(state)
        async for evt in run_graph(state):
            if evt.get("type") == "__final__":
                final_state = evt["state"]
                continue
            yield evt

        await self._persist(final_state, message_id=message_id, trace_id=trace_id)

    async def _persist(self, state: dict[str, Any], *, message_id: str, trace_id: str) -> None:
        async with AsyncSessionLocal() as session:
            try:
                messages = MessageRepository(session)
                msg = await messages.get(message_id)
                if msg is not None:
                    await messages.update(
                        msg,
                        content=_synthesize_content(state),
                        artifacts=_artifacts(state),
                        trace_id=trace_id,
                    )

                execs = AgentExecutionRepository(session)
                for record in state.get("executions", []):
                    await execs.create(
                        message_id=message_id,
                        node_name=record.get("node_name", ""),
                        agent_name=record.get("agent_name", ""),
                        status=record.get("status", "success"),
                        attempt=record.get("attempt", 1),
                        latency_ms=record.get("latency_ms"),
                        trace_id=trace_id,
                        output_payload=record.get("output_payload"),
                        error=record.get("error"),
                    )

                report = state.get("report") or {}
                if report.get("file_path"):
                    await ReportRepository(session).create(
                        project_id=report.get("project_id") or state.get("project_id"),
                        message_id=message_id,
                        title=report.get("title", "Analysis Report"),
                        format=ReportFormat(report.get("format", "pdf")),
                        file_path=report["file_path"],
                        payload=state.get("insights", {}),
                    )
                await session.commit()
            except Exception as exc:  # noqa: BLE001
                await session.rollback()
                logger.error("analytics_persist_failed", error=str(exc))
