"""SQL data-source adapter (Postgres / MySQL / SQLite via SQLAlchemy)."""

from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine

from app.core.config import settings
from app.core.exceptions import DataSourceError
from app.core.logging import get_logger
from app.schemas.datasource import ColumnInfo, TableSchema
from app.services.data_sources.base import DataSourceAdapter
from app.tools.sql_tool import run_sql

logger = get_logger(__name__)


class SQLDataSourceAdapter(DataSourceAdapter):
    """Adapter over an external SQL database addressed by a connection URI."""

    def __init__(self, connection_uri: str, *, engine: Engine | None = None) -> None:
        if not connection_uri and engine is None:
            raise DataSourceError("connection_uri is required for SQLDataSourceAdapter.")
        self._uri = connection_uri
        try:
            self._engine = engine or create_engine(connection_uri, future=True)
        except Exception as exc:  # noqa: BLE001
            raise DataSourceError(f"Failed to create engine: {exc}") from exc

    @property
    def engine(self) -> Engine:
        return self._engine

    def introspect_schema(self) -> list[TableSchema]:
        """Introspect tables/columns via :func:`sqlalchemy.inspect`."""
        try:
            inspector = inspect(self._engine)
            schemas: list[TableSchema] = []
            for table_name in inspector.get_table_names():
                columns = [
                    ColumnInfo(
                        name=str(col["name"]),
                        type=str(col.get("type", "")),
                        nullable=bool(col.get("nullable", True)),
                    )
                    for col in inspector.get_columns(table_name)
                ]
                schemas.append(TableSchema(table=table_name, columns=columns))
            logger.info("sql_schema_introspected", tables=len(schemas))
            return schemas
        except Exception as exc:  # noqa: BLE001
            logger.error("sql_introspect_failed", error=str(exc))
            raise DataSourceError(f"Schema introspection failed: {exc}") from exc

    def run_query(self, sql: str) -> dict[str, Any]:
        """Run a validated read-only query against the engine."""
        return run_sql(sql, engine=self._engine)

    def load_dataframe(self, table: str | None = None) -> pd.DataFrame:
        """Load a table into a DataFrame (capped by ``max_sql_rows``)."""
        if not table:
            raise DataSourceError("A table name is required to load a DataFrame.")
        try:
            result = run_sql(
                f"SELECT * FROM {table}",
                engine=self._engine,
                max_rows=settings.max_sql_rows,
            )
            return pd.DataFrame(result["rows"])
        except DataSourceError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.error("sql_load_dataframe_failed", table=table, error=str(exc))
            raise DataSourceError(f"Failed to load table '{table}': {exc}") from exc

    def close(self) -> None:
        try:
            self._engine.dispose()
        except Exception as exc:  # noqa: BLE001
            logger.warning("sql_engine_dispose_failed", error=str(exc))


__all__ = ["SQLDataSourceAdapter"]
