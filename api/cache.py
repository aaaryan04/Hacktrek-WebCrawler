"""Small thread-safe TTL cache for GET scan endpoints.

Reconnaissance endpoints are idempotent for a given target over a short window,
so repeatedly scanning the same ``(endpoint, url)`` within seconds just hammers
the target for no benefit. This module offers a tiny time-to-live cache that can
wrap those handlers.

It is intentionally dependency-free and self-contained so it can be adopted with
zero risk to existing behaviour. Two ways to use it:

1. As a decorator on a *pure-ish* endpoint (results depend only on its args)::

       from api.cache import ttl_cache

       @app.get("/tech")
       @ttl_cache(ttl_seconds=30)
       def tech_detector(url: str = Query(...)):
           ...

   The cache key is derived from the function name + the bound arguments, so
   different endpoints and different URLs never collide. ``HTTPException`` and
   other errors are never cached (only successful returns are stored).

2. Manually, via a shared :class:`TTLCache` instance::

       cache = TTLCache(ttl_seconds=30)
       hit = cache.get(("tech", url))
       if hit is None:
           hit = do_work()
           cache.set(("tech", url), hit)

Set the default TTL through the ``SCAN_CACHE_TTL`` env var (seconds; ``0``
disables caching).
"""

from __future__ import annotations

import functools
import os
import threading
import time
from typing import Any, Callable, Hashable


def _default_ttl() -> float:
    try:
        return float(os.getenv("SCAN_CACHE_TTL", "0"))
    except (TypeError, ValueError):
        return 0.0


class TTLCache:
    """A minimal thread-safe cache with per-entry expiry and a size cap."""

    def __init__(self, ttl_seconds: float | None = None, max_entries: int = 256):
        self.ttl = _default_ttl() if ttl_seconds is None else float(ttl_seconds)
        self.max_entries = max_entries
        self._store: dict[Hashable, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    @property
    def enabled(self) -> bool:
        return self.ttl > 0

    def get(self, key: Hashable) -> Any | None:
        if not self.enabled:
            return None
        now = time.monotonic()
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if expires_at < now:
                self._store.pop(key, None)
                return None
            return value

    def set(self, key: Hashable, value: Any) -> None:
        if not self.enabled:
            return
        now = time.monotonic()
        with self._lock:
            # Evict expired entries first, then the oldest if still over cap.
            if len(self._store) >= self.max_entries:
                expired = [k for k, (exp, _) in self._store.items() if exp < now]
                for k in expired:
                    self._store.pop(k, None)
                while len(self._store) >= self.max_entries:
                    oldest = min(self._store, key=lambda k: self._store[k][0])
                    self._store.pop(oldest, None)
            self._store[key] = (now + self.ttl, value)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


def ttl_cache(ttl_seconds: float | None = None, max_entries: int = 256) -> Callable:
    """Decorator that memoizes a function's return value for ``ttl_seconds``.

    Only successful returns are cached; raised exceptions propagate uncached.
    The cache instance is attached to the wrapper as ``.cache`` for inspection
    or manual invalidation in tests.
    """

    cache = TTLCache(ttl_seconds=ttl_seconds, max_entries=max_entries)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not cache.enabled:
                return func(*args, **kwargs)
            key = (func.__qualname__, args, tuple(sorted(kwargs.items())))
            cached = cache.get(key)
            if cached is not None:
                return cached
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result

        wrapper.cache = cache  # type: ignore[attr-defined]
        return wrapper

    return decorator
