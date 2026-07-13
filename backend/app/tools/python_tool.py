"""Restricted Python evaluation tool over a pandas DataFrame.

Runs a small, sandboxed Python snippet with a DataFrame named ``df`` in scope
and returns a JSON-serializable result. Builtins are heavily restricted: no
imports, file access, or attribute-based escapes are permitted. This is a
best-effort sandbox intended for trusted-but-generated analysis snippets, not a
security boundary against a hostile adversary.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from langchain_core.tools import tool

from app.core.exceptions import DataSourceError
from app.core.logging import get_logger

logger = get_logger(__name__)

#: Whitelisted builtins exposed to the snippet.
_SAFE_BUILTINS: dict[str, Any] = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "filter": filter,
    "float": float,
    "int": int,
    "len": len,
    "list": list,
    "map": map,
    "max": max,
    "min": min,
    "range": range,
    "round": round,
    "set": set,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "zip": zip,
}

#: Substrings that indicate an attempted sandbox escape.
_BLOCKED_TOKENS = (
    "__",
    "import",
    "open(",
    "exec(",
    "eval(",
    "compile(",
    "globals(",
    "locals(",
    "getattr",
    "setattr",
    "delattr",
    "os.",
    "sys.",
    "subprocess",
)


def _to_jsonable(value: Any) -> Any:
    """Best-effort conversion of a snippet result to JSON-serializable data."""
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return None if (math.isnan(value) or math.isinf(value)) else value
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        f = float(value)
        return None if (math.isnan(f) or math.isinf(f)) else f
    if isinstance(value, np.ndarray):
        return [_to_jsonable(v) for v in value.tolist()]
    if isinstance(value, pd.DataFrame):
        return value.replace({np.nan: None}).to_dict(orient="records")
    if isinstance(value, pd.Series):
        return value.replace({np.nan: None}).to_dict()
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_jsonable(v) for v in value]
    return str(value)


def run_python(code: str, df: pd.DataFrame) -> Any:
    """Evaluate ``code`` with ``df`` in scope and return a JSON-serializable result.

    The snippet may either be a single expression (its value is returned) or a
    block of statements that assigns a ``result`` variable.
    """
    if not code or not code.strip():
        raise DataSourceError("Empty Python snippet.")

    lowered = code.lower()
    for token in _BLOCKED_TOKENS:
        if token in lowered:
            raise DataSourceError(f"Disallowed token in snippet: {token!r}")

    safe_globals: dict[str, Any] = {
        "__builtins__": _SAFE_BUILTINS,
        "pd": pd,
        "np": np,
    }
    safe_locals: dict[str, Any] = {"df": df}

    try:
        try:
            # Prefer expression evaluation.
            value = eval(code, safe_globals, safe_locals)  # noqa: S307
        except SyntaxError:
            # Fall back to statement execution expecting a `result` variable.
            exec(code, safe_globals, safe_locals)  # noqa: S102
            value = safe_locals.get("result")
        result = _to_jsonable(value)
        logger.info("python_snippet_executed", rows=len(df))
        return result
    except DataSourceError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("python_snippet_failed", error=str(exc))
        raise DataSourceError(f"Python snippet failed: {exc}") from exc


def _impl(code: str) -> str:
    """Execute a restricted Python snippet (no DataFrame bound).

    This LLM-facing wrapper runs against an empty DataFrame; graph nodes should
    call :func:`run_python` directly to bind real data. Returns a string
    representation of the result.
    """
    return str(run_python(code, pd.DataFrame()))


python_tool = tool(_impl)

__all__ = ["python_tool", "run_python"]
