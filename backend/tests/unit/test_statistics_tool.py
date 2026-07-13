"""Unit tests for the statistics engine."""

from __future__ import annotations

import pandas as pd
import pytest

from app.tools.statistics_tool import correlations, describe_columns, full_report

pytestmark = pytest.mark.unit


@pytest.fixture
def df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "revenue": [100, 200, 300, 400, 500],
            "cost": [50, 100, 150, 200, 250],
            "region": ["NA", "NA", "EU", "EU", "APAC"],
        }
    )


def test_describe_columns(df: pd.DataFrame) -> None:
    summaries = {s.column: s for s in describe_columns(df)}
    assert "revenue" in summaries
    assert summaries["revenue"].mean == pytest.approx(300)
    assert summaries["revenue"].min == 100


def test_correlations_detects_linear(df: pd.DataFrame) -> None:
    corrs = correlations(df)
    pair = next((c for c in corrs if {c.a, c.b} == {"revenue", "cost"}), None)
    assert pair is not None
    assert pair.coefficient == pytest.approx(1.0, abs=1e-6)


def test_full_report_shape(df: pd.DataFrame) -> None:
    report = full_report(df)
    assert report.summaries
    assert isinstance(report.trends, list)
