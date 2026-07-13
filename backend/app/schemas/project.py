"""Project schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedSchema


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    description: str | None = None


class ProjectRead(TimestampedSchema):
    name: str
    description: str | None
    owner_id: str
