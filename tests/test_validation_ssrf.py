"""Input validation, URL normalization, and SSRF-protection tests.

None of these hit the network: rejection happens in ``normalize_url`` before any
fetch, and the one "valid host" path is covered by the ``public_dns`` fake.
"""

import pytest
from fastapi import HTTPException

import api.server as server


# --------------------------------------------------------------------------- #
# Endpoint-level input validation
# --------------------------------------------------------------------------- #


def test_missing_url_returns_422(client):
    # `url` is a required query param -> FastAPI validation error.
    resp = client.get("/headers")
    assert resp.status_code == 422


@pytest.mark.parametrize("endpoint", ["/headers", "/assessment", "/tls", "/forms"])
def test_missing_url_all_scan_endpoints(client, endpoint):
    assert client.get(endpoint).status_code == 422


# --------------------------------------------------------------------------- #
# SSRF blocking through the HTTP layer
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "target",
    [
        "localhost",
        "http://localhost",
        "http://127.0.0.1",
        "http://192.168.1.10",
        "http://10.0.0.5",
        "http://169.254.169.254",  # cloud metadata endpoint
        "http://[::1]",
        "mybox.local",
        "http://0.0.0.0",
    ],
)
def test_ssrf_targets_blocked(client, target):
    resp = client.get("/headers", params={"url": target})
    assert resp.status_code == 400


# --------------------------------------------------------------------------- #
# normalize_url unit behaviour
# --------------------------------------------------------------------------- #


def test_normalize_adds_https_scheme(public_dns):
    assert server.normalize_url("example.com") == "https://example.com"


def test_normalize_preserves_http_scheme(public_dns):
    assert server.normalize_url("http://example.com/path") == "http://example.com/path"


def test_normalize_strips_whitespace(public_dns):
    assert server.normalize_url("  example.com  ") == "https://example.com"


def test_normalize_empty_rejected():
    with pytest.raises(HTTPException) as exc:
        server.normalize_url("   ")
    assert exc.value.status_code == 400


def test_normalize_localhost_rejected():
    with pytest.raises(HTTPException) as exc:
        server.normalize_url("http://localhost")
    assert exc.value.status_code == 400


def test_normalize_dotlocal_rejected():
    with pytest.raises(HTTPException) as exc:
        server.normalize_url("http://printer.local")
    assert exc.value.status_code == 400


def test_normalize_private_literal_ip_rejected():
    with pytest.raises(HTTPException) as exc:
        server.normalize_url("http://192.168.0.1")
    assert exc.value.status_code == 400


def test_normalize_domain_resolving_private_rejected(monkeypatch):
    """A public-looking domain that DNS-resolves to a private IP is blocked."""

    def _resolves_private(host, *args, **kwargs):
        return [(2, 1, 6, "", ("10.1.2.3", 0))]

    monkeypatch.setattr(server.socket, "getaddrinfo", _resolves_private)
    with pytest.raises(HTTPException) as exc:
        server.normalize_url("http://internal.example.com")
    assert exc.value.status_code == 400


def test_is_blocked_ip_helper():
    assert server._is_blocked_ip("127.0.0.1")
    assert server._is_blocked_ip("192.168.1.1")
    assert server._is_blocked_ip("10.0.0.1")
    assert server._is_blocked_ip("169.254.169.254")
    assert not server._is_blocked_ip("93.184.216.34")  # example.com
    assert not server._is_blocked_ip("8.8.8.8")
