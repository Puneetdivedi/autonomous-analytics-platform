"""SQLAlchemy declarative base and common column mixins."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def _uuid() -> str:
    return str(uuid.uuid4())


class UUIDMixin:
    """Adds a string UUID primary key."""

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)


class TimestampMixin:
    """Adds created_at / updated_at columns managed by the DB."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
