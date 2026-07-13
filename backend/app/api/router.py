"""Top-level API router aggregating all route modules.

The ``chat``, ``agents`` and ``traces`` modules are owned by another team; they
are included opportunistically so that this router still works even if those
modules are not yet present.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import (
    auth,
    datasources,
    feedback,
    health,
    projects,
    reports,
    users,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

api_router = APIRouter()

# Health probes are mounted at the root (no extra prefix).
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(users.router, prefix="/users")
api_router.include_router(projects.router, prefix="/projects")
api_router.include_router(datasources.router, prefix="/datasources")
api_router.include_router(reports.router, prefix="/reports")
api_router.include_router(feedback.router, prefix="/feedback")

# --- Routes provided by another team (optional at import time) ---
try:
    from app.api.routes import agents, chat, traces
except ImportError as exc:  # pragma: no cover - modules may not exist yet
    logger.warning("api.optional_routes_missing", error=str(exc))
else:
    api_router.include_router(chat.router, prefix="/chats")
    api_router.include_router(agents.router, prefix="/agents")
    api_router.include_router(traces.router, prefix="/traces")

__all__ = ["api_router"]
