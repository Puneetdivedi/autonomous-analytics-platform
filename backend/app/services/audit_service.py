"""Audit logging service."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.audit_log_repo import AuditLogRepository


class AuditService:
    """Writes immutable audit-log entries for security-relevant actions."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit = AuditLogRepository(session)

    @staticmethod
    async def log(
        session: AsyncSession,
        user_id: str | None,
        action: str,
        *,
        resource_type: str | None = None,
        resource_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Persist an audit-log entry.

        Static so it can be called with any session without instantiating the
        service (``AuditService.log(session, ...)``).
        """
        repo = AuditLogRepository(session)
        return await repo.create(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata_=metadata,
        )

    async def record(
        self,
        user_id: str | None,
        action: str,
        **kwargs: Any,
    ) -> AuditLog:
        """Instance-based convenience wrapper around :meth:`log`."""
        return await self.log(self.session, user_id, action, **kwargs)
