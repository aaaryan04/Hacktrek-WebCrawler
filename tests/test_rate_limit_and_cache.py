"""Tests for the supporting rate-limit and TTL-cache modules."""

import time

from api.cache import TTLCache, ttl_cache
from api.rate_limit import SlidingWindowLimiter


# --------------------------------------------------------------------------- #
# Rate limiter
# --------------------------------------------------------------------------- #


def test_limiter_disabled_when_zero():
    limiter = SlidingWindowLimiter(limit=0)
    assert not limiter.enabled
    for _ in range(1000):
        allowed, remaining, retry = limiter.check("1.2.3.4")
        assert allowed and remaining == -1 and retry == 0.0


def test_limiter_allows_up_to_limit_then_blocks():
    limiter = SlidingWindowLimiter(limit=3, window_seconds=60)
    key = "9.9.9.9"
    assert limiter.check(key)[0] is True
    assert limiter.check(key)[0] is True
    assert limiter.check(key)[0] is True
    allowed, remaining, retry = limiter.check(key)
    assert allowed is False
    assert remaining == 0
    assert retry > 0


def test_limiter_is_per_key():
    limiter = SlidingWindowLimiter(limit=1, window_seconds=60)
    assert limiter.check("a")[0] is True
    assert limiter.check("a")[0] is False
    assert limiter.check("b")[0] is True  # different IP unaffected


def test_limiter_window_expiry():
    limiter = SlidingWindowLimiter(limit=1, window_seconds=0.05)
    assert limiter.check("k")[0] is True
    assert limiter.check("k")[0] is False
    time.sleep(0.06)
    assert limiter.check("k")[0] is True


def test_middleware_returns_429(monkeypatch):
    """With RATE_LIMIT_PER_MINUTE=1 the second request gets a 429."""
    import importlib

    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "1")
    import api.rate_limit as rl

    importlib.reload(rl)
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()
    app.add_middleware(rl.RateLimitMiddleware)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    c = TestClient(app)
    assert c.get("/ping").status_code == 200
    blocked = c.get("/ping")
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers

    # Restore default module state for the rest of the suite.
    monkeypatch.delenv("RATE_LIMIT_PER_MINUTE", raising=False)
    importlib.reload(rl)


# --------------------------------------------------------------------------- #
# TTL cache
# --------------------------------------------------------------------------- #


def test_cache_disabled_by_default():
    cache = TTLCache(ttl_seconds=0)
    assert not cache.enabled
    cache.set("k", 1)
    assert cache.get("k") is None


def test_cache_hit_and_expiry():
    cache = TTLCache(ttl_seconds=0.05)
    cache.set(("tech", "example.com"), {"result": 1})
    assert cache.get(("tech", "example.com")) == {"result": 1}
    time.sleep(0.06)
    assert cache.get(("tech", "example.com")) is None


def test_cache_key_isolation():
    cache = TTLCache(ttl_seconds=30)
    cache.set(("tech", "a.com"), "A")
    cache.set(("headers", "a.com"), "H")
    assert cache.get(("tech", "a.com")) == "A"
    assert cache.get(("headers", "a.com")) == "H"


def test_ttl_cache_decorator_memoizes():
    calls = {"n": 0}

    @ttl_cache(ttl_seconds=30)
    def work(url):
        calls["n"] += 1
        return {"url": url}

    assert work("x") == {"url": "x"}
    assert work("x") == {"url": "x"}
    assert calls["n"] == 1  # second call served from cache
    assert work("y") == {"url": "y"}
    assert calls["n"] == 2


def test_ttl_cache_decorator_passthrough_when_disabled():
    calls = {"n": 0}

    @ttl_cache(ttl_seconds=0)
    def work(url):
        calls["n"] += 1
        return url

    work("x")
    work("x")
    assert calls["n"] == 2  # no caching when disabled
