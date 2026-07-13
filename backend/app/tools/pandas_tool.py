"""Pandas helper utilities.

Small, dependency-light helpers shared by loaders, adapters, and the statistics
engine: building DataFrames from query rows, profiling a DataFrame, and
converting a DataFrame back to JSON-serializable records.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.core.exceptions import DataSourceError
from app.core.logging import get_logger

logger = get_logger(__name__)


def dataframe_from_rows(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Build a DataFrame from a list of row dicts (as returned by the SQL tool)."""
    try:
        return pd.DataFrame(rows or [])
    except Exception as exc:  # noqa: BLE001
        logger.error("dataframe_from_rows_failed", error=str(exc))
        raise DataSourceError(f"Failed to build DataFrame from rows: {exc}") from exc


def to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert a DataFrame to JSON-serializable records (NaN -> ``None``)."""
    if df is None or df.empty:
        return []
    try:
        cleaned = df.replace({np.nan: None})
        return cleaned.to_dict(orient="records")
    except Exception as exc:  # noqa: BLE001
        logger.error("to_records_failed", error=str(exc))
        raise DataSourceError(f"Failed to convert DataFrame to records: {exc}") from exc


def profile_dataframe(df: pd.DataFrame) -> dict[str, Any]:
    """Return a lightweight profile: shape, dtypes, null counts and describe()."""
    if df is None:
        raise DataSourceError("Cannot profile a None DataFrame.")

    try:
        dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
        null_counts = {col: int(df[col].isna().sum()) for col in df.columns}

        describe: dict[str, Any] = {}
        if not df.empty:
            numeric = df.select_dtypes(include=[np.number])
            if not numeric.empty:
                described = numeric.describe().replace({np.nan: None})
                describe = {
                    str(col): {str(k): v for k, v in described[col].to_dict().items()}
                    for col in described.columns
                }

        return {
            "shape": {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
            "columns": list(map(str, df.columns)),
            "dtypes": dtypes,
            "null_counts": null_counts,
            "describe": describe,
        }
    except DataSourceError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("profile_dataframe_failed", error=str(exc))
        raise DataSourceError(f"Failed to profile DataFrame: {exc}") from exc


__all__ = ["dataframe_from_rows", "to_records", "profile_dataframe"]
