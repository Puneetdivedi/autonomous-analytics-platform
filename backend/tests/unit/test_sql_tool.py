"""Unit tests for the SQL tool (safety + execution)."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text

from app.core.exceptions import SQLValidationError
from app.tools.sql_tool import run_sql, validate_sql

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "bad_sql",
    ["DELETE FROM users", "DROP TABLE t", "UPDATE t SET x=1", "SELECT 1; DROP TABLE t"],
)
def test_validate_rejects_non_select(bad_sql: str) -> None:
    with pytest.raises(SQLValidationError):
        validate_sql(bad_sql)


def test_validate_allows_select() -> None:
    assert "SELECT" in validate_sql("SELECT * FROM t").upper()


def test_run_sql_executes_and_limits() -> None:
    engine = create_engine("sqlite://", future=True)
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE sales (region TEXT, amount INT)"))
        conn.execute(text("INSERT INTO sales VALUES ('NA', 100), ('EU', 200)"))
    result = run_sql("SELECT region, amount FROM sales ORDER BY amount", engine=engine)
    assert result["row_count"] == 2
    assert result["columns"] == ["region", "amount"]
    assert result["rows"][0]["region"] == "NA"
