"""User schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr

from app.models.enums import UserRole
from app.schemas.common import TimestampedSchema


class UserRead(TimestampedSchema):
    email: EmailStr
    full_name: str | None
    role: UserRole
    is_active: bool
    is_superuser: bool


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None
