"""Chat & message schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import MessageRole
from app.schemas.common import TimestampedSchema


class ChatCreate(BaseModel):
    project_id: str
    title: str = Field(default="New chat", max_length=255)


class ChatRead(TimestampedSchema):
    project_id: str
    title: str


class MessageRead(TimestampedSchema):
    chat_id: str
    role: MessageRole
    content: str
    artifacts: dict[str, Any] | None
    trace_id: str | None


class ChatWithMessages(ChatRead):
    messages: list[MessageRead] = []


class AskRequest(BaseModel):
    """Post a question to a chat and run the agent graph."""

    question: str = Field(min_length=1)
    datasource_id: str | None = None
    stream: bool = True


class StreamEvent(BaseModel):
    """Server-sent event payload emitted during graph execution."""

    type: str  # node_start | node_end | token | artifact | error | done
    node: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
