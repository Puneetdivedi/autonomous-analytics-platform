"""Access-log middleware — logs method, path, status and duration."""

from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger("app.access")


class AccessLogMiddleware(BaseHTTPMiddleware):
    """Emit one structured log line per HTTP request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "http.request.error",
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration_ms, 2),
                client=request.client.host if request.client else None,
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "http.request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            client=request.client.host if request.client else None,
        )
        return response
