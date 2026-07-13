"""Chat service — conversation CRUD and the question/answer orchestration."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.database.session import AsyncSessionLocal
from app.models.chat import Chat
from app.models.enums import MessageRole
from app.models.message import Message
from app.repositories.chat_repo import ChatRepository
from app.repositories.message_repo import MessageRepository
from app.services.analytics_service import AnalyticsService

logger = get_logger(__name__)


class ChatService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.chats = ChatRepository(session)
        self.messages = MessageRepository(session)

    async def create_chat(self, project_id: str, title: str = "New chat") -> Chat:
        chat = await self.chats.create(project_id=project_id, title=title)
        await self.session.commit()
        return chat

    async def list_chats(self, project_id: str) -> list[Chat]:
        return await self.chats.list_for_project(project_id)

    async def get_with_messages(self, chat_id: str) -> Chat:
        chat = await self.chats.get_with_messages(chat_id)
        if chat is None:
            await self.chats.get_or_404(chat_id)  # raises NotFoundError
        return chat  # type: ignore[return-value]

    async def _prepare_turn(self, chat_id: str, question: str) -> tuple[Message, Message, str]:
        """Persist the user message and an assistant placeholder in a fresh session."""
        async with AsyncSessionLocal() as session:
            chat = await ChatRepository(session).get_or_404(chat_id)
            repo = MessageRepository(session)
            user_msg = await repo.create(chat_id=chat_id, role=MessageRole.USER, content=question)
            assistant_msg = await repo.create(
                chat_id=chat_id, role=MessageRole.ASSISTANT, content=""
            )
            await session.commit()
            return user_msg, assistant_msg, chat.project_id

    async def ask_stream(
        self,
        *,
        chat_id: str,
        question: str,
        user_id: str,
        datasource_id: str | None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Yield StreamEvent dicts for a question; persists the answer at the end."""
        user_msg, assistant_msg, project_id = await self._prepare_turn(chat_id, question)
        yield {
            "type": "message_created",
            "node": None,
            "data": {"user_message_id": user_msg.id, "assistant_message_id": assistant_msg.id},
        }

        analytics = AnalyticsService()
        async for evt in analytics.stream(
            question=question,
            project_id=project_id,
            chat_id=chat_id,
            message_id=assistant_msg.id,
            user_id=user_id,
            datasource_id=datasource_id,
        ):
            yield evt
