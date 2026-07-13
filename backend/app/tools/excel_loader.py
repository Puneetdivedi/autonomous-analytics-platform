"""Excel loading utilities (openpyxl backend)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.core.exceptions import DataSourceError
from app.core.logging import get_logger

logger = get_logger(__name__)


def list_sheets(path: str | Path) -> list[str]:
    """Return the sheet names present in an Excel workbook."""
    file_path = Path(path)
    if not file_path.exists():
        raise DataSourceError(f"Excel file not found: {file_path}")
    try:
        with pd.ExcelFile(file_path, engine="openpyxl") as xls:
            return list(xls.sheet_names)
    except Exception as exc:  # noqa: BLE001
        logger.error("excel_list_sheets_failed", path=str(file_path), error=str(exc))
        raise DataSourceError(f"Failed to list sheets in '{file_path}': {exc}") from exc


def load_excel(
    path: str | Path,
    sheet: str | int | None = None,
    **kwargs: object,
) -> pd.DataFrame:
    """Load a single sheet of an Excel workbook into a DataFrame.

    When ``sheet`` is ``None`` the first sheet is loaded. Extra keyword
    arguments are forwarded to :func:`pandas.read_excel`.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise DataSourceError(f"Excel file not found: {file_path}")
    sheet_name: str | int = 0 if sheet is None else sheet
    try:
        df = pd.read_excel(
            file_path, sheet_name=sheet_name, engine="openpyxl", **kwargs  # type: ignore[arg-type]
        )
        logger.info(
            "excel_loaded",
            path=str(file_path),
            sheet=str(sheet_name),
            rows=len(df),
            cols=df.shape[1],
        )
        return df
    except Exception as exc:  # noqa: BLE001
        logger.error("excel_load_failed", path=str(file_path), error=str(exc))
        raise DataSourceError(f"Failed to load Excel '{file_path}': {exc}") from exc


__all__ = ["load_excel", "list_sheets"]
