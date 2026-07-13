"""Common/shared Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ORMModel(BaseModel):
    """Base for schemas read from ORM objects."""

    model_config = ConfigDict(from_attributes=True)


class TimestampedSchema(ORMModel):
    id: str
    created_at: datetime
    updated_at: datetime


class Page(BaseModel, Generic[T]):
    """Generic paginated response."""

    items: list[T]
    total: int
    page: int = 1
    size: int = 20


class Message(BaseModel):
    """Simple message response."""

    detail: str


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    environment: str
    services: dict[str, str] = Field(default_factory=dict)
