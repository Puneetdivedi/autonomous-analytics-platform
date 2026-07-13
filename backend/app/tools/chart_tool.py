"""Chart rendering tool.

Renders a :class:`ChartSpec` to a base64-encoded PNG using matplotlib with the
headless ``Agg`` backend (no GUI, safe for servers). Also builds Recharts-shaped
data from a DataFrame for the frontend.
"""

from __future__ import annotations

import base64
import io
from typing import Any

import matplotlib

matplotlib.use("Agg")  # Headless backend — must be set before pyplot import.

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from langchain_core.tools import tool  # noqa: E402

from app.core.exceptions import DataSourceError  # noqa: E402
from app.core.logging import get_logger  # noqa: E402
from app.schemas.analysis import ChartSpec  # noqa: E402

logger = get_logger(__name__)

_SUPPORTED = {"bar", "line", "pie", "scatter", "histogram", "heatmap", "area"}


def build_chart_data(df: pd.DataFrame, x: str, y: str | list[str]) -> list[dict[str, Any]]:
    """Build Recharts-friendly records: ``[{x: v, y1: v, y2: v}, ...]``."""
    if df is None or df.empty:
        return []
    y_cols = [y] if isinstance(y, str) else list(y)
    keep = [x, *y_cols]
    missing = [c for c in keep if c not in df.columns]
    if missing:
        raise DataSourceError(f"Columns not in DataFrame: {missing}")
    try:
        subset = df[keep].replace({np.nan: None})
        return subset.to_dict(orient="records")
    except Exception as exc:  # noqa: BLE001
        logger.error("build_chart_data_failed", error=str(exc))
        raise DataSourceError(f"Failed to build chart data: {exc}") from exc


def _y_columns(spec: ChartSpec) -> list[str]:
    if spec.y is None:
        return []
    return [spec.y] if isinstance(spec.y, str) else list(spec.y)


def _render(spec: ChartSpec, ax: plt.Axes, df: pd.DataFrame) -> None:
    """Draw the chart described by ``spec`` onto ``ax``."""
    chart_type = spec.type
    x = spec.x
    y_cols = _y_columns(spec)

    if chart_type == "bar":
        x_vals = df[x] if x and x in df else df.index
        for col in y_cols:
            ax.bar(x_vals.astype(str), df[col], label=col)
    elif chart_type == "line":
        x_vals = df[x] if x and x in df else df.index
        for col in y_cols:
            ax.plot(x_vals, df[col], marker="o", label=col)
    elif chart_type == "area":
        x_vals = df[x] if x and x in df else df.index
        for col in y_cols:
            ax.fill_between(range(len(df)), df[col], alpha=0.4, label=col)
        ax.set_xticks(range(len(df)))
        ax.set_xticklabels([str(v) for v in x_vals], rotation=45, ha="right")
    elif chart_type == "scatter":
        if len(y_cols) < 1 or not x:
            raise DataSourceError("Scatter chart requires 'x' and one 'y' column.")
        ax.scatter(df[x], df[y_cols[0]], alpha=0.7)
        ax.set_xlabel(x)
        ax.set_ylabel(y_cols[0])
    elif chart_type == "histogram":
        col = y_cols[0] if y_cols else x
        if not col or col not in df:
            raise DataSourceError("Histogram requires a numeric column.")
        ax.hist(df[col].dropna(), bins="auto")
        ax.set_xlabel(col)
    elif chart_type == "pie":
        col = y_cols[0] if y_cols else None
        if not col or col not in df:
            raise DataSourceError("Pie chart requires a 'y' value column.")
        labels = df[x].astype(str) if x and x in df else df.index.astype(str)
        ax.pie(df[col], labels=list(labels), autopct="%1.1f%%")
        ax.axis("equal")
    elif chart_type == "heatmap":
        numeric = df.select_dtypes(include=[np.number])
        if numeric.empty:
            raise DataSourceError("Heatmap requires numeric columns.")
        matrix = numeric.corr()
        im = ax.imshow(matrix.values, cmap="viridis", aspect="auto")
        ax.set_xticks(range(len(matrix.columns)))
        ax.set_xticklabels(matrix.columns, rotation=45, ha="right")
        ax.set_yticks(range(len(matrix.index)))
        ax.set_yticklabels(matrix.index)
        ax.figure.colorbar(im, ax=ax)
    else:  # pragma: no cover - guarded by caller
        raise DataSourceError(f"Unsupported chart type: {chart_type}")

    if chart_type in {"bar", "line", "area"} and y_cols:
        ax.legend()
        if chart_type == "bar" and x:
            for label in ax.get_xticklabels():
                label.set_rotation(45)
                label.set_ha("right")


def render_chart(spec: ChartSpec) -> str:
    """Render ``spec`` to a base64-encoded PNG string.

    The chart's data is taken from ``spec.data`` (a list of record dicts).
    Returns the base64 payload (no ``data:`` URI prefix). Raises
    :class:`DataSourceError` on unsupported types or empty data.
    """
    if spec.type not in _SUPPORTED:
        raise DataSourceError(f"Unsupported chart type: {spec.type}")
    if not spec.data:
        raise DataSourceError("ChartSpec has no data to render.")

    df = pd.DataFrame(spec.data)
    fig, ax = plt.subplots(figsize=(8, 5))
    try:
        _render(spec, ax, df)
        ax.set_title(spec.title)
        fig.tight_layout()

        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=120, bbox_inches="tight")
        buffer.seek(0)
        encoded = base64.b64encode(buffer.read()).decode("ascii")
        logger.info("chart_rendered", type=spec.type, points=len(df))
        return encoded
    except DataSourceError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("chart_render_failed", type=spec.type, error=str(exc))
        raise DataSourceError(f"Failed to render chart: {exc}") from exc
    finally:
        plt.close(fig)


def _impl(spec: dict[str, Any]) -> str:
    """Render a chart from a ChartSpec-shaped dict; returns a base64 PNG string."""
    return render_chart(ChartSpec.model_validate(spec))


chart_tool = tool(_impl)

__all__ = ["chart_tool", "render_chart", "build_chart_data"]
