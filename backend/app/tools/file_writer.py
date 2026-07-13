"""Filesystem write helpers scoped to the configured storage directories.

All writes are confined to ``settings.report_dir`` or ``settings.upload_dir``
(a relative path is resolved under the chosen base). Parent directories are
created automatically. Attempts to escape the base directory are rejected.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from app.core.config import settings
from app.core.exceptions import DataSourceError
from app.core.logging import get_logger

logger = get_logger(__name__)

Base = Literal["report", "upload"]


def _base_dir(base: Base) -> Path:
    return Path(settings.report_dir if base == "report" else settings.upload_dir)


def resolve_path(path: str | Path, base: Base = "report") -> Path:
    """Resolve ``path`` under the chosen base dir, rejecting traversal escapes."""
    base_dir = _base_dir(base).resolve()
    candidate = Path(path)
    target = candidate if candidate.is_absolute() else base_dir / candidate
    target = target.resolve()

    try:
        target.relative_to(base_dir)
    except ValueError as exc:
        raise DataSourceError(
            f"Refusing to write outside '{base}' directory: {target}"
        ) from exc
    return target


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_bytes(path: str | Path, data: bytes, *, base: Base = "report") -> str:
    """Write raw bytes to ``path`` (under the base dir). Returns the absolute path."""
    target = resolve_path(path, base)
    try:
        _ensure_parent(target)
        target.write_bytes(data)
        logger.info("file_written", path=str(target), bytes=len(data))
        return str(target)
    except DataSourceError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("write_bytes_failed", path=str(target), error=str(exc))
        raise DataSourceError(f"Failed to write file '{target}': {exc}") from exc


def write_text(
    path: str | Path,
    text: str,
    *,
    base: Base = "report",
    encoding: str = "utf-8",
) -> str:
    """Write text to ``path`` (under the base dir). Returns the absolute path."""
    target = resolve_path(path, base)
    try:
        _ensure_parent(target)
        target.write_text(text, encoding=encoding)
        logger.info("file_written", path=str(target), chars=len(text))
        return str(target)
    except DataSourceError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("write_text_failed", path=str(target), error=str(exc))
        raise DataSourceError(f"Failed to write file '{target}': {exc}") from exc


__all__ = ["write_bytes", "write_text", "resolve_path"]
