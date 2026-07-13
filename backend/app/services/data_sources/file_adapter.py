"""File data-source adapter (CSV / Excel).

Loads an uploaded file into a pandas DataFrame and registers it in an in-memory
SQLite database (via ``df.to_sql``) so the same SELECT-only SQL tooling used for
real databases works transparently over uploaded files. A ``StaticPool`` keeps
the in-memory database alive across connections.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from app.core.exceptions import DataSourceError
from app.core.logging import get_logger
from app.models.enums import DataSourceType
from app.schemas.datasource import TableSchema
from app.services.data_sources.base import DataSourceAdapter
from app.tools.csv_loader import infer_schema, load_csv
from app.tools.excel_loader import load_excel
from app.tools.sql_tool import run_sql

logger = get_logger(__name__)


def _sanitize_table_name(name: str) -> str:
    """Produce a safe SQL identifier from a file stem."""
    cleaned = re.sub(r"\W+", "_", name).strip("_").lower()
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"t_{cleaned}"
    return cleaned or "data"


class FileDataSourceAdapter(DataSourceAdapter):
    """Adapter over an uploaded CSV/Excel file, queryable via in-memory SQLite."""

    def __init__(
        self,
        file_path: str | Path,
        type: DataSourceType,
        *,
        sheet: str | int | None = None,
    ) -> None:
        self._path = Path(file_path)
        self._type = type
        self._sheet = sheet
        self._table = _sanitize_table_name(self._path.stem)
        self._df: pd.DataFrame | None = None
        self._engine: Engine | None = None

    # --- Loading ------------------------------------------------------------

    def _load(self) -> pd.DataFrame:
        if self._df is not None:
            return self._df
        if self._type == DataSourceType.CSV:
            self._df = load_csv(self._path)
        elif self._type == DataSourceType.EXCEL:
            self._df = load_excel(self._path, sheet=self._sheet)
        else:
            raise DataSourceError(f"FileDataSourceAdapter does not support type '{self._type}'.")
        return self._df

    def _get_engine(self) -> Engine:
        if self._engine is not None:
            return self._engine
        df = self._load()
        try:
            engine = create_engine(
                "sqlite://",
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                future=True,
            )
            df.to_sql(self._table, engine, index=False, if_exists="replace")
            self._engine = engine
            logger.info("file_registered_in_sqlite", table=self._table, rows=len(df))
            return engine
        except Exception as exc:  # noqa: BLE001
            logger.error("file_sqlite_register_failed", error=str(exc))
            raise DataSourceError(f"Failed to register file in SQLite: {exc}") from exc

    # --- Adapter API --------------------------------------------------------

    @property
    def table_name(self) -> str:
        return self._table

    def introspect_schema(self) -> list[TableSchema]:
        """Infer the schema directly from the loaded DataFrame."""
        df = self._load()
        return [infer_schema(df, self._table)]

    def run_query(self, sql: str) -> dict[str, Any]:
        """Run a validated read-only query over the in-memory SQLite table."""
        return run_sql(sql, engine=self._get_engine())

    def load_dataframe(self, table: str | None = None) -> pd.DataFrame:
        """Return the loaded DataFrame (``table`` is ignored — single source)."""
        return self._load().copy()

    def close(self) -> None:
        if self._engine is not None:
            try:
                self._engine.dispose()
            except Exception as exc:  # noqa: BLE001
                logger.warning("file_engine_dispose_failed", error=str(exc))


__all__ = ["FileDataSourceAdapter"]
