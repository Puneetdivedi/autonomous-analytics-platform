"""Structured-output schemas for agents.

These are the Pydantic contracts agents produce via LLM structured output. They
are stored (as dicts) in :class:`app.graphs.state.AnalyticsState` and surfaced to
the frontend as message artifacts.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


# --- Intent ---
class Intent(BaseModel):
    type: Literal[
        "descriptive", "diagnostic", "comparative", "trend", "forecast", "adhoc"
    ] = "adhoc"
    entities: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    time_range: str | None = None
    filters: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.5, ge=0, le=1)


# --- Plan ---
class PlanStep(BaseModel):
    step: int
    node: str
    description: str


class Plan(BaseModel):
    steps: list[PlanStep]
    rationale: str = ""


# --- Metadata ---
class RelevantSchema(BaseModel):
    relevant_tables: list[str]
    reasoning: str = ""


# --- SQL ---
class GeneratedSQL(BaseModel):
    sql: str
    dialect: str = "postgresql"
    explanation: str = ""


class SQLValidation(BaseModel):
    is_valid: bool
    is_safe: bool
    issues: list[str] = Field(default_factory=list)
    corrected_sql: str | None = None


# --- Statistics ---
class StatisticSummary(BaseModel):
    column: str
    mean: float | None = None
    median: float | None = None
    mode: float | None = None
    std: float | None = None
    variance: float | None = None
    min: float | None = None
    max: float | None = None
    outliers: list[float] = Field(default_factory=list)


class Correlation(BaseModel):
    a: str
    b: str
    coefficient: float
    method: str = "pearson"


class Regression(BaseModel):
    target: str
    feature: str
    slope: float
    intercept: float
    r_squared: float


class Forecast(BaseModel):
    column: str
    horizon: int
    values: list[float]
    method: str = "linear"


class StatisticsReport(BaseModel):
    summaries: list[StatisticSummary] = Field(default_factory=list)
    correlations: list[Correlation] = Field(default_factory=list)
    regressions: list[Regression] = Field(default_factory=list)
    forecasts: list[Forecast] = Field(default_factory=list)
    trends: list[str] = Field(default_factory=list)


# --- Charts ---
ChartType = Literal["bar", "line", "pie", "scatter", "histogram", "heatmap", "area"]


class ChartSpec(BaseModel):
    type: ChartType
    title: str
    x: str | None = None
    y: str | list[str] | None = None
    # Data prepared for Recharts on the frontend.
    data: list[dict[str, Any]] = Field(default_factory=list)
    # Optional server-rendered PNG (base64) for report embedding.
    image_b64: str | None = None


class ChartPlan(BaseModel):
    """Wrapper so agents can return multiple charts via structured output."""

    charts: list[ChartSpec] = Field(default_factory=list)


# --- Insights ---
class Insights(BaseModel):
    executive_summary: str
    key_findings: list[str] = Field(default_factory=list)
    root_cause: str = ""
    risks: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)


# --- Recommendations ---
class Recommendation(BaseModel):
    title: str
    detail: str
    impact: Literal["low", "medium", "high"] = "medium"
    effort: Literal["low", "medium", "high"] = "medium"


class RecommendationSet(BaseModel):
    """Wrapper so agents can return multiple recommendations via structured output."""

    recommendations: list[Recommendation] = Field(default_factory=list)


# --- Reflection ---
class Reflection(BaseModel):
    quality_score: float = Field(ge=0, le=1)
    needs_retry: bool = False
    retry_target: str | None = None  # node name to jump back to
    feedback: str = ""
