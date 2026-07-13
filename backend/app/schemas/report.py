"""Report & feedback schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.enums import FeedbackRating, ReportFormat
from app.schemas.common import TimestampedSchema


class ReportCreate(BaseModel):
    project_id: str
    message_id: str | None = None
    title: str = Field(max_length=255)
    format: ReportFormat = ReportFormat.PDF


class ReportRead(TimestampedSchema):
    project_id: str
    message_id: str | None
    title: str
    format: ReportFormat
    file_path: str


class FeedbackCreate(BaseModel):
    message_id: str
    rating: FeedbackRating
    comment: str | None = None


class FeedbackRead(TimestampedSchema):
    message_id: str
    user_id: str
    rating: FeedbackRating
    comment: str | None
