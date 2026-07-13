"""CSV loading and schema inference."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.core.exceptions import DataSourceError
from app.core.logging import get_logger
from app.schemas.datasource import ColumnInfo, TableSchema

logger = get_logger(__name__)

# Treat blanks and explicit null sentinels as missing, but NOT "NA"/"N/A"/"n/a":
# in enterprise data those frequently mean a real category (e.g. "NA" = North
# America), and pandas' default would silently drop them to NaN.
_NA_VALUES = [
    "",
    "#N/A",
    "#N/A N/A",
    "#NA",
    "-NaN",
    "-nan",
    "<NA>",
    "NULL",
    "NaN",
    "None",
    "nan",
    "null",
]


def load_csv(path: str | Path, **kwargs: object) -> pd.DataFrame:
    """Load a CSV file into a DataFrame.

    Extra keyword arguments are forwarded to :func:`pandas.read_csv`. By default
    the ambiguous ``NA``/``N/A`` tokens are preserved as literal strings; pass
    ``keep_default_na=True`` to restore pandas' default behavior.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise DataSourceError(f"CSV file not found: {file_path}")
    kwargs.setdefault("keep_default_na", False)  # type: ignore[arg-type]
    kwargs.setdefault("na_values", _NA_VALUES)  # type: ignore[arg-type]
    try:
        df = pd.read_csv(file_path, **kwargs)  # type: ignore[arg-type]
        logger.info("csv_loaded", path=str(file_path), rows=len(df), cols=df.shape[1])
        return df
    except Exception as exc:  # noqa: BLE001
        logger.error("csv_load_failed", path=str(file_path), error=str(exc))
        raise DataSourceError(f"Failed to load CSV '{file_path}': {exc}") from exc


def infer_schema(df: pd.DataFrame, table_name: str) -> TableSchema:
    """Infer a :class:`TableSchema` from a DataFrame's dtypes."""
    try:
        columns = [
            ColumnInfo(
                name=str(col),
                type=str(df[col].dtype),
                nullable=bool(df[col].isna().any()),
            )
            for col in df.columns
        ]
        return TableSchema(
            table=table_name,
            columns=columns,
            row_estimate=int(df.shape[0]),
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("infer_schema_failed", table=table_name, error=str(exc))
        raise DataSourceError(f"Failed to infer schema for '{table_name}': {exc}") from exc


__all__ = ["load_csv", "infer_schema"]
