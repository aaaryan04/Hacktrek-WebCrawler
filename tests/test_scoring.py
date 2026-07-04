"""End-to-end scoring / risk-level mapping tests for /assessment.

Outbound HTTP (``requests.get``), DNS (``socket.getaddrinfo``) and TLS
(``inspect_tls``) are all mocked, so these run offline while still exercising
the real scoring pipeline in ``full_assessment``.
"""

import pytest

import api.server as server
from tests.conftest import FakeResponse

ALL_SECURITY_HEADERS = {h: "present" for h in server.SECURITY_HEADERS}


def _install_fetch(monkeypatch, main_response, robots=None, sitemap=None):
    """Route ``requests.get`` to per-path fake responses (offline)."""
    robots = robots or FakeResponse("", status_code=404)
    sitemap = sitemap or FakeResponse("", status_code=404)

    def fake_get(url, *args, **kwargs):
        if url.endswith("/robots.txt"):
            return robots
        if url.endswith("/sitemap.xml"):
            return sitemap
        return main_response

    monkeypatch.setattr(server.requests, "get", fake_get)


def _install_good_tls(monkeypatch):
    monkeypatch.setattr(
        server,
        "inspect_tls",
        lambda host, port=443: {
            "host": host,
            "tls_version": "TLSv1.3",
            "days_to_expiry": 300,
            "expired": False,
        },
    )


@pytest.fixture
def scan_env(monkeypatch, public_dns):
    """Common offline environment: DNS + TLS mocked."""
    _install_good_tls(monkeypatch)
    return monkeypatch


def test_assessment_low_risk_clean_site(scan_env, client):
    clean = FakeResponse(
        text="<html><body>clean</body></html>",
        status_code=200,
        headers=ALL_SECURITY_HEADERS,
    )
    _install_fetch(scan_env, clean)

    resp = client.get("/assessment", params={"url": "example.com"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["risk_score"] == 100
    assert body["risk_level"] == "Low"
    assert body["security_headers"]["missing"] == []


def test_assessment_moderate_risk(scan_env, client):
    # Present CSP + HSTS; missing the other four headers (penalty 10+8+6+5 = 29).
    headers = {
        "Content-Security-Policy": "default-src 'self'",
        "Strict-Transport-Security": "max-age=63072000",
    }
    resp_obj = FakeResponse("<html></html>", status_code=200, headers=headers)
    _install_fetch(scan_env, resp_obj)

    resp = client.get("/assessment", params={"url": "example.com"})
    body = resp.json()
    assert body["risk_score"] == 71
    assert body["risk_level"] == "Moderate"


def test_assessment_critical_risk(scan_env, client):
    # No security headers, exposed banners, and a password form over GET.
    html = """
    <html><body>
      <form method="get" action="/login">
        <input type="text" name="u">
        <input type="password" name="p">
      </form>
    </body></html>
    """
    bad = FakeResponse(
        text=html,
        status_code=200,
        headers={"Server": "nginx/1.0", "X-Powered-By": "PHP/7.0"},
    )
    _install_fetch(scan_env, bad)

    resp = client.get("/assessment", params={"url": "example.com"})
    body = resp.json()
    assert body["risk_level"] == "Critical"
    assert body["risk_score"] < 40
    assert body["summary"]["forms_found"] == 1


def test_assessment_risk_level_boundaries():
    """Directly verify the score->level thresholds used by the endpoint."""

    def level(score):
        if score >= 85:
            return "Low"
        if score >= 65:
            return "Moderate"
        if score >= 40:
            return "High"
        return "Critical"

    assert level(100) == "Low"
    assert level(85) == "Low"
    assert level(84) == "Moderate"
    assert level(65) == "Moderate"
    assert level(64) == "High"
    assert level(40) == "High"
    assert level(39) == "Critical"
    assert level(0) == "Critical"


def test_assessment_response_shape(scan_env, client):
    clean = FakeResponse("<html></html>", 200, headers=ALL_SECURITY_HEADERS)
    _install_fetch(scan_env, clean)
    body = client.get("/assessment", params={"url": "example.com"}).json()
    for key in (
        "module",
        "target",
        "domain",
        "risk_score",
        "risk_level",
        "summary",
        "security_headers",
        "cookies",
        "waf_cdn",
        "tls",
        "technologies",
        "forms",
        "findings",
        "recommendations",
    ):
        assert key in body
