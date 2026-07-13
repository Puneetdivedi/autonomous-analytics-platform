"""Data-access repositories.

Each repository wraps an :class:`~sqlalchemy.ext.asyncio.AsyncSession` and
exposes async CRUD helpers over a single ORM model. Services depend on these
rather than touching the session directly, keeping the persistence layer thin
and easily testable.
"""

from __future__ import annotations

from app.repositories.agent_execution_repo import AgentExecutionRepository
from app.repositories.audit_log_repo import AuditLogRepository
from app.repositories.base import BaseRepository
from app.repositories.chat_repo import ChatRepository
from app.repositories.datasource_repo import DataSourceRepository
from app.repositories.feedback_repo import FeedbackRepository
from app.repositories.message_repo import MessageRepository
from app.repositories.project_repo import ProjectRepository
from app.repositories.prompt_version_repo import PromptVersionRepository
from app.repositories.report_repo import ReportRepository
from app.repositories.user_repo import UserRepository

__all__ = [
    "AgentExecutionRepository",
    "AuditLogRepository",
    "BaseRepository",
    "ChatRepository",
    "DataSourceRepository",
    "FeedbackRepository",
    "MessageRepository",
    "ProjectRepository",
    "PromptVersionRepository",
    "ReportRepository",
    "UserRepository",
]
