"""A dependency-free stub chat model for local demos and tests.

Activated with ``LLM_PROVIDER=stub``. It implements only the two surfaces the
agents actually use — ``with_structured_output(schema).ainvoke(...)`` and
``ainvoke(...)`` — and returns schema-valid, *context-aware* outputs by parsing
the JSON blocks the agents embed in their prompts (schema, result columns,
sample rows, pre-computed statistics). This lets the full LangGraph supervisor
stream end-to-end with no API key, producing coherent (if templated) results.
"""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import AIMessage
from pydantic import BaseModel

from app.schemas.analysis import (
    ChartPlan,
    ChartSpec,
    GeneratedSQL,
    Insights,
    Intent,
    Plan,
    PlanStep,
    Recommendation,
    RecommendationSet,
    Reflection,
    RelevantSchema,
    SQLValidation,
    StatisticsReport,
)

_NUMERIC_HINTS = ("int", "float", "num", "real", "double", "dec", "money")


def _human_text(messages: list[Any]) -> str:
    for msg in reversed(messages):
        content = getattr(msg, "content", None)
        if content:
            return str(content)
    return ""


def _segment_after(text: str, marker: str) -> str:
    """Return the block following a ``marker`` line (prompts join parts with \\n\\n)."""
    for seg in text.split("\n\n"):
        if marker in seg:
            return seg.split("\n", 1)[1].strip() if "\n" in seg else ""
    return ""


def _load(text: str, marker: str) -> Any:
    try:
        return json.loads(_segment_after(text, marker))
    except (ValueError, TypeError):
        return None


def _tables(schema_json: Any) -> list[tuple[str, list[tuple[str, str]]]]:
    """Normalize either schema shape into ``[(table, [(col, type)])]``."""
    out: list[tuple[str, list[tuple[str, str]]]] = []
    if isinstance(schema_json, dict) and "tables" in schema_json:
        for t in schema_json["tables"]:
            cols = [(c.get("name"), c.get("type", "")) for c in t.get("columns", [])]
            out.append((t.get("table"), cols))
    elif isinstance(schema_json, dict):
        for name, cols in schema_json.items():
            if isinstance(cols, list):
                out.append((name, [(c.get("name"), c.get("type", "")) for c in cols]))
    return out


def _is_numeric_type(type_str: str) -> bool:
    return any(h in (type_str or "").lower() for h in _NUMERIC_HINTS)


def _is_numeric_value(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


class _StructuredRunnable:
    """Mimics the object returned by ``BaseChatModel.with_structured_output``."""

    def __init__(self, schema: type[BaseModel]) -> None:
        self._schema = schema

    async def ainvoke(self, messages: list[Any], **_: Any) -> BaseModel:
        return _build(self._schema, _human_text(messages))


class StubChatModel:
    """Minimal stand-in for a LangChain chat model (no network, no key)."""

    def with_structured_output(self, schema: type[BaseModel], **_: Any) -> _StructuredRunnable:
        return _StructuredRunnable(schema)

    async def ainvoke(self, messages: list[Any], **_: Any) -> AIMessage:
        return AIMessage(content="[stub-llm] response")


# --- Per-schema builders -------------------------------------------------------


def _build(schema: type[BaseModel], text: str) -> BaseModel:
    builder = _BUILDERS.get(schema.__name__)
    if builder is not None:
        try:
            return builder(text)
        except Exception:  # noqa: BLE001 - never let the stub break a demo
            pass
    # Fallback: construct with defaults.
    return schema()  # type: ignore[call-arg]


def _build_intent(text: str) -> Intent:
    q = _segment_after(text, "User question:") or text
    return Intent(
        type="diagnostic",
        entities=re.findall(r"North America|NA|EU|APAC", q) or ["overall"],
        metrics=["revenue"] if "revenue" in q.lower() else ["value"],
        time_range="recent period",
        confidence=0.9,
    )


def _build_plan(_: str) -> Plan:
    nodes = [
        ("metadata", "Identify the relevant tables and columns."),
        ("sql_generator", "Write a read-only SQL query to retrieve the metric."),
        ("sql_validator", "Validate the SQL is safe and correct."),
        ("execution", "Execute the query against the data source."),
        ("statistical_analysis", "Compute descriptive statistics and trends."),
        ("visualization", "Select and render the most informative chart."),
        ("insight", "Explain the finding and its root cause."),
        ("recommendation", "Recommend concrete business actions."),
    ]
    return Plan(
        steps=[PlanStep(step=i + 1, node=n, description=d) for i, (n, d) in enumerate(nodes)],
        rationale="Diagnostic question — retrieve the metric, quantify the change, explain it.",
    )


def _build_relevant_schema(text: str) -> RelevantSchema:
    tables = _tables(_load(text, "schema") or _load(text, "Full datasource schema"))
    names = [t[0] for t in tables] or ["dataset"]
    return RelevantSchema(
        relevant_tables=names[:2], reasoning="Tables containing the requested metric."
    )


def _build_generated_sql(text: str) -> GeneratedSQL:
    dialect_seg = _segment_after(text, "Target SQL dialect:")
    dialect = dialect_seg.strip() or "postgresql"
    tables = _tables(_load(text, "Schema (tables -> columns):") or _load(text, "schema"))
    if not tables:
        return GeneratedSQL(
            sql="SELECT 1 AS value LIMIT 1", dialect=dialect, explanation="No schema available."
        )
    table, cols = tables[0]
    nums = [c for c, t in cols if _is_numeric_type(t)]
    cats = [c for c, t in cols if not _is_numeric_type(t)]
    if nums and cats:
        sql = (
            f'SELECT "{cats[0]}", SUM("{nums[0]}") AS "{nums[0]}" '
            f'FROM "{table}" GROUP BY "{cats[0]}" ORDER BY 2 DESC LIMIT 100'
        )
        expl = f"Aggregate {nums[0]} by {cats[0]} to compare segments."
    else:
        sql = f'SELECT * FROM "{table}" LIMIT 100'
        expl = "Sample the table to inspect the metric."
    return GeneratedSQL(sql=sql, dialect=dialect, explanation=expl)


def _build_sql_validation(_: str) -> SQLValidation:
    return SQLValidation(is_valid=True, is_safe=True, issues=[])


def _build_statistics(text: str) -> StatisticsReport:
    stats = _load(text, "Pre-computed statistics")
    if isinstance(stats, dict):
        return StatisticsReport(**stats)
    return StatisticsReport(trends=["Values differ meaningfully across segments."])


def _columns_and_rows(text: str) -> tuple[list[str], list[dict[str, Any]]]:
    cols = _load(text, "Result columns:") or []
    rows = _load(text, "Result rows sample") or []
    return (cols if isinstance(cols, list) else []), (rows if isinstance(rows, list) else [])


def _build_chart_plan(text: str) -> ChartPlan:
    cols, rows = _columns_and_rows(text)
    if not cols:
        return ChartPlan(charts=[])
    row0 = rows[0] if rows else {}
    nums = [c for c in cols if _is_numeric_value(row0.get(c))]
    cats = [c for c in cols if not _is_numeric_value(row0.get(c))]
    x = cats[0] if cats else cols[0]
    y = nums[0] if nums else (cols[1] if len(cols) > 1 else cols[0])
    return ChartPlan(charts=[ChartSpec(type="bar", title=f"{y} by {x}", x=x, y=y)])


def _build_insights(text: str) -> Insights:
    q = _segment_after(text, "User question:") or "the metric"
    return Insights(
        executive_summary=(
            f"Analysis of “{q.strip()}” shows a clear difference across segments, "
            "with one segment accounting for the majority of the change."
        ),
        key_findings=[
            "The leading segment dominates the total metric.",
            "A secondary segment shows the largest relative movement.",
            "The trend is consistent with the pre-computed statistics.",
        ],
        root_cause=(
            "The movement is driven primarily by volume differences between segments "
            "rather than by a change in unit economics."
        ),
        risks=["Continued softness in the declining segment could compound next period."],
        opportunities=["Reallocate investment toward the most resilient segment."],
    )


def _build_recommendations(_: str) -> RecommendationSet:
    return RecommendationSet(
        recommendations=[
            Recommendation(
                title="Launch a targeted win-back campaign",
                detail=(
                    "Focus on the declining segment with tailored offers to recover lost volume."
                ),
                impact="high",
                effort="medium",
            ),
            Recommendation(
                title="Double down on the resilient segment",
                detail=(
                    "Shift marketing spend toward the segment showing stable or growing "
                    "performance."
                ),
                impact="medium",
                effort="low",
            ),
        ]
    )


def _build_reflection(_: str) -> Reflection:
    return Reflection(
        quality_score=0.88,
        needs_retry=False,
        feedback="Answer is well-supported by the data and statistics.",
    )


_BUILDERS = {
    "Intent": _build_intent,
    "Plan": _build_plan,
    "RelevantSchema": _build_relevant_schema,
    "GeneratedSQL": _build_generated_sql,
    "SQLValidation": _build_sql_validation,
    "StatisticsReport": _build_statistics,
    "ChartPlan": _build_chart_plan,
    "Insights": _build_insights,
    "RecommendationSet": _build_recommendations,
    "Reflection": _build_reflection,
}
