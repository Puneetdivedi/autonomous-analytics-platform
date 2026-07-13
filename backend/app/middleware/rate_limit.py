"""Per-IP token-bucket rate limiting.

Uses an in-process token bucket by default. If a Redis URL is configured and
``redis.asyncio`` is importable, a shared bucket is kept in Redis so the limit
holds across workers; any Redis failure degrades gracefully back to the local
in-memory bucket (fail-open) so a Redis outage never takes the API down.
"""

from __future__ import annotations

import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.logging import get_logger

logger = get_logger("app.rate_limit")


class _LocalBucket:
    """Monotonic-clock token bucket keyed by client identity."""

    def __init__(self, rate: float, capacity: int) -> None:
        self.rate = rate
        self.capacity = capacity
        # key -> (tokens, last_refill_ts)
        self._state: dict[str, tuple[float, float]] = defaultdict(
            lambda: (float(capacity), time.monotonic())
        )

    def allow(self, key: str) -> bool:
        tokens, last = self._state[key]
        now = time.monotonic()
        tokens = min(self.capacity, tokens + (now - last) * self.rate)
        if tokens >= 1.0:
            self._state[key] = (tokens - 1.0, now)
            return True
        self._state[key] = (tokens, now)
        return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Token-bucket limiter, ``capacity`` requests refilling at ``rate``/sec."""

    def __init__(
        self,
        app,
        *,
        capacity: int = 100,
        rate_per_second: float = 20.0,
        redis_url: str | None = None,
        exempt_paths: tuple[str, ...] = ("/health", "/ready", "/docs", "/openapi.json"),
    ) -> None:
        super().__init__(app)
        self.capacity = capacity
        self.rate_per_second = rate_per_second
        self.exempt_paths = exempt_paths
        self._local = _LocalBucket(rate_per_second, capacity)
        self._redis = None
        if redis_url:
            try:
                import redis.asyncio as aioredis  # noqa: PLC0415

                self._redis = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)
            except Exception as exc:  # noqa: BLE001
                logger.warning("rate_limit.redis_unavailable", error=str(exc))
                self._redis = None

    def _client_key(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def _allow_redis(self, key: str) -> bool | None:
        """Best-effort Redis fixed-window check. ``None`` signals fall-through."""
        if self._redis is None:
            return None
        window = max(1, int(self.capacity / max(self.rate_per_second, 1e-9)))
        redis_key = f"ratelimit:{key}"
        try:
            count = await self._redis.incr(redis_key)
            if count == 1:
                await self._redis.expire(redis_key, window)
            return count <= self.capacity
        except Exception as exc:  # noqa: BLE001 — degrade gracefully
            logger.warning("rate_limit.redis_error", error=str(exc))
            return None

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if any(request.url.path.startswith(p) for p in self.exempt_paths):
            return await call_next(request)

        key = self._client_key(request)
        allowed = await self._allow_redis(key)
        if allowed is None:
            allowed = self._local.allow(key)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error_code": "rate_limit",
                    "message": "Too many requests",
                    "details": {},
                },
                headers={"Retry-After": "1"},
            )
        return await call_next(request)
