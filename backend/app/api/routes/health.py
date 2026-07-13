"""Health & readiness probes."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DbSession
from app.core.config import settings
from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
async def health() -> HealthResponse:
    """Return basic liveness information; does not touch dependencies."""
    return HealthResponse(
        status="ok",
        version="0.1.0",
        environment=settings.environment,
    )


@router.get("/ready", response_model=HealthResponse, summary="Readiness probe")
async def ready(db: DbSession) -> HealthResponse:
    """Return readiness, pinging the database connection."""
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        db_status = "error"

    return HealthResponse(
        status="ok" if db_status == "ok" else "degraded",
        version="0.1.0",
        environment=settings.environment,
        services={"database": db_status},
    )
