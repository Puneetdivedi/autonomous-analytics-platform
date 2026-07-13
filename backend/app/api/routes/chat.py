"""Chat routes — conversation management and the streaming Q&A endpoint."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse

from app.api.deps import ActiveUser, DbSession
from app.models.message import Message as MessageModel
from app.repositories.message_repo import MessageRepository
from app.schemas.chat import (
    AskRequest,
    ChatCreate,
    ChatRead,
    ChatWithMessages,
    MessageRead,
)
from app.services.chat_service import ChatService

router = APIRouter(tags=["chat"])


@router.post(
    "",
    response_model=ChatRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create chat",
)
async def create_chat(payload: ChatCreate, db: DbSession, _: ActiveUser) -> ChatRead:
    chat = await ChatService(db).create_chat(payload.project_id, payload.title)
    return ChatRead.model_validate(chat)


@router.get("", response_model=list[ChatRead], summary="List chats for a project")
async def list_chats(project_id: str, db: DbSession, _: ActiveUser) -> list[ChatRead]:
    chats = await ChatService(db).list_chats(project_id)
    return [ChatRead.model_validate(c) for c in chats]


@router.get("/{chat_id}", response_model=ChatWithMessages, summary="Get chat with messages")
async def get_chat(chat_id: str, db: DbSession, _: ActiveUser) -> ChatWithMessages:
    chat = await ChatService(db).get_with_messages(chat_id)
    return ChatWithMessages.model_validate(chat)


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event, default=str)}\n\n"


@router.post("/{chat_id}/messages", summary="Ask a question (SSE stream)")
async def ask(chat_id: str, payload: AskRequest, db: DbSession, user: ActiveUser):
    service = ChatService(db)

    if payload.stream:

        async def event_stream() -> AsyncIterator[str]:
            async for evt in service.ask_stream(
                chat_id=chat_id,
                question=payload.question,
                user_id=user.id,
                datasource_id=payload.datasource_id,
            ):
                yield _sse(evt)

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # Non-streaming: drain the generator, then return the final assistant message.
    assistant_id: str | None = None
    async for evt in service.ask_stream(
        chat_id=chat_id,
        question=payload.question,
        user_id=user.id,
        datasource_id=payload.datasource_id,
    ):
        if evt.get("type") == "message_created":
            assistant_id = evt["data"]["assistant_message_id"]

    msg: MessageModel | None = None
    if assistant_id:
        msg = await MessageRepository(db).get(assistant_id)
    return MessageRead.model_validate(msg) if msg else {"detail": "completed"}
