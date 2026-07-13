"""Numeric analysis engine.

Pure-numeric functions over :class:`pandas.DataFrame` producing the Pydantic
statistics schemas. Everything is guarded against empty / non-numeric / NaN
data so agents never crash on messy inputs.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from app.core.exceptions import DataSourceError
from app.core.logging import get_logger
from app.schemas.analysis import (
    Correlation,
    Forecast,
    Regression,
    StatisticsReport,
    StatisticSummary,
)

logger = get_logger(__name__)


def _finite(value: Any) -> float | None:
    """Return a plain float or ``None`` for NaN/inf/non-numeric values."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return f


def _numeric_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Return the numeric sub-frame, raising on a None input."""
    if df is None:
        raise DataSourceError("DataFrame is None.")
    return df.select_dtypes(include=[np.number])


def _iqr_outliers(series: pd.Series) -> list[float]:
    """Return values outside the 1.5*IQR fences (capped at 50 values)."""
    clean = series.dropna()
    if len(clean) < 4:
        return []
    q1 = clean.quantile(0.25)
    q3 = clean.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0:
        return []
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    mask = (clean < lower) | (clean > upper)
    outliers = [f for f in (_finite(v) for v in clean[mask].tolist()) if f is not None]
    return outliers[:50]


def describe_columns(df: pd.DataFrame) -> list[StatisticSummary]:
    """Per-column summary statistics for every numeric column."""
    numeric = _numeric_frame(df)
    if numeric.empty:
        return []

    summaries: list[StatisticSummary] = []
    for col in numeric.columns:
        series = numeric[col].dropna()
        if series.empty:
            summaries.append(StatisticSummary(column=str(col)))
            continue
        try:
            mode_series = series.mode()
            mode_val = _finite(mode_series.iloc[0]) if not mode_series.empty else None
            summaries.append(
                StatisticSummary(
                    column=str(col),
                    mean=_finite(series.mean()),
                    median=_finite(series.median()),
                    mode=mode_val,
                    std=_finite(series.std(ddof=1)) if len(series) > 1 else 0.0,
                    variance=_finite(series.var(ddof=1)) if len(series) > 1 else 0.0,
                    min=_finite(series.min()),
                    max=_finite(series.max()),
                    outliers=_iqr_outliers(series),
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("describe_column_failed", column=str(col), error=str(exc))
            summaries.append(StatisticSummary(column=str(col)))
    return summaries


def correlations(df: pd.DataFrame, *, threshold: float = 0.0) -> list[Correlation]:
    """Pearson correlation for every unique numeric column pair."""
    numeric = _numeric_frame(df)
    if numeric.shape[1] < 2:
        return []
    try:
        matrix = numeric.corr(method="pearson")
    except Exception as exc:  # noqa: BLE001
        logger.warning("correlation_failed", error=str(exc))
        return []

    pairs: list[Correlation] = []
    cols = list(matrix.columns)
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            coeff = _finite(matrix.iloc[i, j])
            if coeff is None or abs(coeff) < threshold:
                continue
            pairs.append(Correlation(a=str(cols[i]), b=str(cols[j]), coefficient=coeff))
    return pairs


def linear_regression(df: pd.DataFrame, target: str, feature: str) -> Regression:
    """Ordinary least-squares regression of ``target`` on a single ``feature``."""
    if df is None or target not in df.columns or feature not in df.columns:
        raise DataSourceError("Target/feature column not found for regression.")

    pair = df[[feature, target]].apply(pd.to_numeric, errors="coerce").dropna()
    if len(pair) < 2:
        raise DataSourceError("Not enough numeric data points for regression.")

    x = pair[feature].to_numpy(dtype=float)
    y = pair[target].to_numpy(dtype=float)
    try:
        slope, intercept = np.polyfit(x, y, 1)
        predicted = slope * x + intercept
        ss_res = float(np.sum((y - predicted) ** 2))
        ss_tot = float(np.sum((y - y.mean()) ** 2))
        r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
        return Regression(
            target=str(target),
            feature=str(feature),
            slope=_finite(slope) or 0.0,
            intercept=_finite(intercept) or 0.0,
            r_squared=_finite(r_squared) or 0.0,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("regression_failed", error=str(exc))
        raise DataSourceError(f"Regression failed: {exc}") from exc


def forecast(series: pd.Series | list[float], horizon: int = 5) -> Forecast:
    """Forecast ``horizon`` future values via a simple linear (polyfit) trend."""
    if horizon < 1:
        raise DataSourceError("Forecast horizon must be >= 1.")

    name = "series"
    if isinstance(series, pd.Series):
        name = str(series.name or "series")
        values = pd.to_numeric(series, errors="coerce").dropna().to_numpy(dtype=float)
    else:
        values = np.array([v for v in (_finite(x) for x in series) if v is not None], dtype=float)

    if len(values) < 2:
        raise DataSourceError("Not enough data points to forecast.")

    try:
        idx = np.arange(len(values), dtype=float)
        slope, intercept = np.polyfit(idx, values, 1)
        future_idx = np.arange(len(values), len(values) + horizon, dtype=float)
        predictions = slope * future_idx + intercept
        forecast_values = [_finite(v) or 0.0 for v in predictions.tolist()]
        return Forecast(
            column=name,
            horizon=horizon,
            values=forecast_values,
            method="linear",
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("forecast_failed", error=str(exc))
        raise DataSourceError(f"Forecast failed: {exc}") from exc


def detect_trends(df: pd.DataFrame) -> list[str]:
    """Emit human-readable trend/relationship notes about the numeric columns."""
    numeric = _numeric_frame(df)
    trends: list[str] = []
    if numeric.empty:
        return trends

    for col in numeric.columns:
        series = numeric[col].dropna()
        if len(series) < 3:
            continue
        idx = np.arange(len(series), dtype=float)
        try:
            slope = float(np.polyfit(idx, series.to_numpy(dtype=float), 1)[0])
        except Exception:  # noqa: BLE001
            continue
        spread = float(series.std(ddof=1)) if len(series) > 1 else 0.0
        if abs(slope) < 1e-9 or (spread and abs(slope) < 0.05 * spread):
            direction = "stable"
        else:
            direction = "increasing" if slope > 0 else "decreasing"
        trends.append(f"'{col}' shows a {direction} trend (slope={slope:.4g}).")

    for corr in correlations(df, threshold=0.7):
        strength = "strong positive" if corr.coefficient > 0 else "strong negative"
        trends.append(
            f"'{corr.a}' and '{corr.b}' have a {strength} correlation ({corr.coefficient:.2f})."
        )
    return trends


def full_report(df: pd.DataFrame) -> StatisticsReport:
    """Combine summaries, correlations, regressions, forecasts and trends."""
    numeric = _numeric_frame(df)
    if numeric.empty:
        logger.info("full_report_empty", reason="no numeric columns")
        return StatisticsReport()

    summaries = describe_columns(df)
    corrs = correlations(df)
    trends = detect_trends(df)

    regressions: list[Regression] = []
    forecasts: list[Forecast] = []

    cols = list(numeric.columns)
    # Regress the strongest correlated pair (if any) as an illustrative fit.
    if corrs:
        top = max(corrs, key=lambda c: abs(c.coefficient))
        try:
            regressions.append(linear_regression(df, top.b, top.a))
        except DataSourceError:
            pass

    # Forecast each numeric column with enough history.
    for col in cols:
        series = numeric[col].dropna()
        if len(series) >= 3:
            try:
                forecasts.append(forecast(numeric[col], horizon=5))
            except DataSourceError:
                continue

    logger.info(
        "full_report_built",
        summaries=len(summaries),
        correlations=len(corrs),
        regressions=len(regressions),
        forecasts=len(forecasts),
    )
    return StatisticsReport(
        summaries=summaries,
        correlations=corrs,
        regressions=regressions,
        forecasts=forecasts,
        trends=trends,
    )


__all__ = [
    "describe_columns",
    "correlations",
    "linear_regression",
    "forecast",
    "detect_trends",
    "full_report",
]
