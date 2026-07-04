"""Lightweight in-process per-IP rate limiting for the Hacktrek WebCrawler API.

This module provides a dependency-free sliding-window rate limiter implemented
as a Starlette ``BaseHTTPMiddleware``. It is deliberately simple: state lives in
memory, keyed by client IP, and is safe for a single-process Uvicorn worker
(the default deployment). For multi-worker / multi-instance deployments put a
shared limiter (e.g. Redis, or an API gateway) in front instead.

Configuration is entirely env-driven so it can be tuned or disabled without code
changes:

    RATE_LIMIT_PER_MINUTE   Max requests allowed per client IP per 60s window.
                            ``0`` (the default) disables rate limiting entirely,
                            so existing behaviour is preserved unless opted in.

Wiring (already done in ``api/server.py`` with a single line)::

    from api.rate_limit import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware)

When the limit is exceeded the middleware short-circuits with an HTTP ``429``
JSON body and a ``Retry-After`` header, without ever calling the route handler
(so no outbound scan is triggered).
"""

from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

# Window length in seconds. A per-*minute* limit is the natural unit here.
_WINDOW_SECONDS = 60.0


def _configured_limit() -> int:
    """Read RATE_LIMIT_PER_MINUTE from the environment (0/invalid => disabled)."""
    try:
        return int(os.getenv("RATE_LIMIT_PER_MINUTE", "0"))
    except (TypeError, ValueError):
        return 0


class SlidingWindowLimiter:
    """Thread-safe per-key sliding-window counter.

    Kept independent of the ASGI layer so it can be unit-tested directly.
    """

    def __init__(self, limit: int, window_seconds: float = _WINDOW_SECONDS):
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    @property
    def enabled(self) -> bool:
        return self.limit > 0

    def check(self, key: str, now: float | None = None) -> tuple[bool, int, float]:
        """Register a hit for ``key``.

        Returns ``(allowed, remaining, retry_after_seconds)``. When disabled
        every request is allowed. ``retry_after_seconds`` is the number of
        seconds until the oldest in-window hit ages out (only meaningful when
        the request is rejected).
        """
        if not self.enabled:
            return True, -1, 0.0

        now = time.monotonic() if now is None else now
        cutoff = now - self.window

        with self._lock:
            bucket = self._hits[key]
            # Drop timestamps that have aged out of the window.
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= self.limit:
                retry_after = self.window - (now - bucket[0])
                return False, 0, max(retry_after, 0.0)

            bucket.append(now)
            # Opportunistic cleanup so idle keys don't leak memory forever.
            if not bucket:
                self._hits.pop(key, None)
            return True, self.limit - len(bucket), 0.0

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


def _client_ip(request: Request) -> str:
    """Best-effort client IP, honouring a single X-Forwarded-For hop."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = request.client
    return client.host if client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP sliding-window rate limiting middleware.

    The limit is read from ``RATE_LIMIT_PER_MINUTE`` at construction time. If it
    is ``0`` (default) the middleware is a transparent pass-through.
    """

    def __init__(self, app, limit: int | None = None, window_seconds: float = _WINDOW_SECONDS):
        super().__init__(app)
        resolved = _configured_limit() if limit is None else limit
        self.limiter = SlidingWindowLimiter(resolved, window_seconds)

    async def dispatch(self, request: Request, call_next):
        if not self.limiter.enabled:
            return await call_next(request)

        key = _client_ip(request)
        allowed, remaining, retry_after = self.limiter.check(key)

        if not allowed:
            retry_seconds = int(retry_after) + 1
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too many requests. Please slow down.",
                    "limit_per_minute": self.limiter.limit,
                    "retry_after_seconds": retry_seconds,
                },
                headers={
                    "Retry-After": str(retry_seconds),
                    "X-RateLimit-Limit": str(self.limiter.limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.limiter.limit)
        if remaining >= 0:
            response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
