"""AuditLog repository."""

from __future__ import annotations

from sqlalchemy import select

from app.models.audit_log import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    model = AuditLog

    async def list_for_user(self, user_id: str) -> list[AuditLog]:
        """Return audit log entries for ``user_id`` newest first."""
        stmt = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
