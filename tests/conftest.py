"""Shared pytest fixtures and offline HTTP fakes for the API test suite.

All tests here run **fully offline**. Anything that would touch the network in
``api.server`` (``requests.get`` for page/robots/sitemap fetches,
``socket.getaddrinfo`` for SSRF resolution checks, and ``inspect_tls`` for TLS
handshakes) is monkeypatched to deterministic fakes.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Guarantee the repo root is importable even if pytest.ini pythonpath is ignored.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

import api.server as server  # noqa: E402


class FakeRawHeaders:
    """Mimics urllib3's HTTPHeaderDict.getlist for multi Set-Cookie support."""

    def __init__(self, set_cookies):
        self._set_cookies = list(set_cookies or [])

    def getlist(self, name):
        if name.lower() == "set-cookie":
            return list(self._set_cookies)
        return []


class FakeRaw:
    def __init__(self, set_cookies):
        self.headers = FakeRawHeaders(set_cookies)


class FakeResponse:
    """Minimal stand-in for ``requests.Response`` used throughout the suite."""

    def __init__(self, text="", status_code=200, headers=None, set_cookies=None):
        self.text = text
        self.status_code = status_code
        base = dict(headers or {})
        # Fold any provided Set-Cookie values into the headers mapping too, so
        # code paths that read a single combined header still see something.
        if set_cookies:
            base.setdefault("Set-Cookie", set_cookies[0])
        self.headers = base
        self.raw = FakeRaw(set_cookies)


@pytest.fixture
def fake_response():
    """Factory for building :class:`FakeResponse` objects in tests."""
    return FakeResponse


@pytest.fixture
def public_dns(monkeypatch):
    """Make every hostname resolve to a public IP so SSRF checks pass."""

    def _fake_getaddrinfo(host, *args, **kwargs):
        # 93.184.216.34 == example.com, a routable public address.
        return [(2, 1, 6, "", ("93.184.216.34", 0))]

    monkeypatch.setattr(server.socket, "getaddrinfo", _fake_getaddrinfo)
    return _fake_getaddrinfo


@pytest.fixture
def client():
    """A TestClient with rate limiting neutralised (RATE_LIMIT_PER_MINUTE unset)."""
    return TestClient(server.app)
