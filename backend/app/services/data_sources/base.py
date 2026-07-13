"""Abstract data-source adapter contract.

A :class:`DataSourceAdapter` gives the agent layer a uniform interface over any
backing store (an external SQL database or an uploaded CSV/Excel file):

* :meth:`introspect_schema` — discover tables and columns.
* :meth:`run_query` — run a read-only SQL query and return rows.
* :meth:`load_dataframe` — materialize a table (or the whole source) as a
  :class:`pandas.DataFrame`.

Methods are synchronous because they wrap sync SQLAlchemy engines; call them via
``anyio.to_thread`` / an executor from async graph nodes when needed.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from app.schemas.datasource import TableSchema


class DataSourceAdapter(ABC):
    """Uniform interface over a SQL or file-backed data source."""

    @abstractmethod
    def introspect_schema(self) -> list[TableSchema]:
        """Return the schema (tables + columns) of the data source."""
        raise NotImplementedError

    @abstractmethod
    def run_query(self, sql: str) -> dict[str, Any]:
        """Run a read-only SQL query, returning ``{columns, rows, row_count}``."""
        raise NotImplementedError

    @abstractmethod
    def load_dataframe(self, table: str | None = None) -> pd.DataFrame:
        """Load ``table`` (or the default/only source) into a DataFrame."""
        raise NotImplementedError

    def close(self) -> None:  # pragma: no cover - optional override
        """Release any held resources (engines, connections). No-op by default."""
        return None

    def __enter__(self) -> "DataSourceAdapter":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


__all__ = ["DataSourceAdapter"]
