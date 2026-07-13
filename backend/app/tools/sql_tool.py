"""Read-only SQL execution tool.

Executes a **SELECT-only**, single-statement SQL query against a SQLAlchemy
engine (created from a connection URI) and returns the result set as a plain
dict. Non-SELECT statements, multiple statements, and obviously destructive
keywords are rejected via :mod:`sqlparse` before execution. A ``LIMIT`` is
enforced so agents can never pull unbounded result sets.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

import sqlparse
from langchain_core.tools import tool
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.core.config import settings
from app.core.exceptions import SQLExecutionError, SQLValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)

#: Keywords that must never appear in a read-only query.
_FORBIDDEN = (
    "insert",
    "update",
    "delete",
    "drop",
    "truncate",
    "alter",
    "create",
    "replace",
    "grant",
    "revoke",
    "merge",
    "call",
    "attach",
    "pragma",
)

_LIMIT_RE = re.compile(r"\blimit\b", re.IGNORECASE)


def validate_sql(sql: str) -> str:
    """Validate that ``sql`` is a single, read-only SELECT statement.

    Returns the cleaned SQL (trailing semicolon stripped). Raises
    :class:`SQLValidationError` on any violation.
    """
    if not sql or not sql.strip():
        raise SQLValidationError("Empty SQL statement.")

    statements = [s for s in sqlparse.parse(sql) if str(s).strip()]
    if len(statements) != 1:
        raise SQLValidationError(
            "Only a single SQL statement may be executed.",
            details={"statement_count": len(statements)},
        )

    statement = statements[0]
    stmt_type = statement.get_type()
    first_token = statement.token_first(skip_cm=True)
    first_kw = first_token.value.lower() if first_token is not None else ""

    # Allow plain SELECT and CTE (WITH ... SELECT ...) queries only.
    if stmt_type != "SELECT" and first_kw != "with":
        raise SQLValidationError(
            "Only read-only SELECT queries are permitted.",
            details={"statement_type": stmt_type},
        )

    lowered = sql.lower()
    for keyword in _FORBIDDEN:
        if re.search(rf"\b{keyword}\b", lowered):
            raise SQLValidationError(
                f"Forbidden keyword detected: {keyword!r}.",
                details={"keyword": keyword},
            )

    return sql.strip().rstrip(";").strip()


def _coerce(value: Any) -> Any:
    """Coerce a DB value into something JSON-serializable."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (bytes, bytearray)):
        try:
            return value.decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            return str(value)
    return value


def _enforce_limit(sql: str, max_rows: int) -> str:
    """Append a ``LIMIT`` clause if the query does not already have one."""
    if _LIMIT_RE.search(sql):
        return sql
    return f"{sql} LIMIT {max_rows}"


def run_sql(
    sql: str,
    *,
    connection_uri: str | None = None,
    engine: Engine | None = None,
    max_rows: int | None = None,
) -> dict[str, Any]:
    """Execute a read-only SQL query and return ``{columns, rows, row_count}``.

    Provide either a SQLAlchemy ``engine`` or a ``connection_uri`` (a new sync
    engine is created and disposed for the latter).
    """
    max_rows = max_rows or settings.max_sql_rows
    cleaned = validate_sql(sql)
    limited = _enforce_limit(cleaned, max_rows)

    owns_engine = False
    if engine is None:
        if not connection_uri:
            raise SQLExecutionError("Either 'engine' or 'connection_uri' is required.")
        try:
            engine = create_engine(connection_uri, future=True)
            owns_engine = True
        except Exception as exc:  # noqa: BLE001
            raise SQLExecutionError(f"Failed to create engine: {exc}") from exc

    log = logger.bind(max_rows=max_rows)
    try:
        with engine.connect() as conn:
            result = conn.execute(text(limited))
            columns = list(result.keys())
            rows = [
                {col: _coerce(val) for col, val in zip(columns, row)}
                for row in result.fetchall()
            ]
        log.info("sql_executed", row_count=len(rows), columns=len(columns))
        return {"columns": columns, "rows": rows, "row_count": len(rows)}
    except SQLValidationError:
        raise
    except Exception as exc:  # noqa: BLE001
        log.error("sql_execution_failed", error=str(exc))
        raise SQLExecutionError(f"SQL execution failed: {exc}") from exc
    finally:
        if owns_engine and engine is not None:
            engine.dispose()


def _impl(sql: str, connection_uri: str) -> dict[str, Any]:
    """Run a read-only SELECT query against a database.

    Args:
        sql: A single SELECT (or WITH ... SELECT) statement.
        connection_uri: SQLAlchemy connection URI for the target database.

    Returns:
        A dict with ``columns`` (list[str]), ``rows`` (list[dict]) and
        ``row_count`` (int). Results are capped by the configured row limit.
    """
    return run_sql(sql, connection_uri=connection_uri)


sql_tool = tool(_impl)

__all__ = ["sql_tool", "run_sql", "validate_sql"]
