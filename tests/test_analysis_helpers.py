"""Unit tests for the pure analysis helpers (headers, cookies, tech, forms)."""

from bs4 import BeautifulSoup

import api.server as server
from tests.conftest import FakeResponse


# --------------------------------------------------------------------------- #
# Header analysis
# --------------------------------------------------------------------------- #


def test_analyze_headers_all_present():
    headers = {h: "x" for h in server.SECURITY_HEADERS}
    result = server.analyze_headers(headers)
    assert result["missing"] == []
    assert set(result["present"]) == set(server.SECURITY_HEADERS)
    assert result["penalty"] == 0
    assert result["findings"] == []


def test_analyze_headers_all_missing_penalizes():
    result = server.analyze_headers({})
    assert set(result["missing"]) == set(server.SECURITY_HEADERS)
    expected = sum(meta["points"] for meta in server.SECURITY_HEADERS.values())
    assert result["penalty"] == expected
    assert len(result["findings"]) == len(server.SECURITY_HEADERS)


def test_analyze_headers_flags_banners():
    result = server.analyze_headers({"Server": "nginx/1.2", "X-Powered-By": "PHP/8"})
    titles = {f["title"] for f in result["findings"]}
    assert "Server banner exposed" in titles
    assert "Technology header exposed" in titles


# --------------------------------------------------------------------------- #
# Cookie analysis
# --------------------------------------------------------------------------- #


def test_analyze_cookies_secure_cookie_no_penalty():
    resp = FakeResponse(set_cookies=["sid=abc; Secure; HttpOnly; SameSite=Strict"])
    result = server.analyze_cookies(resp)
    assert result["cookies"][0]["name"] == "sid"
    assert result["cookies"][0]["secure"] is True
    assert result["cookies"][0]["http_only"] is True
    # The parser lower-cases cookie attributes, so SameSite=Strict -> "strict".
    assert result["cookies"][0]["samesite"] == "strict"
    assert result["penalty"] == 0
    assert result["findings"] == []


def test_analyze_cookies_insecure_cookie_penalized():
    resp = FakeResponse(set_cookies=["sid=abc"])
    result = server.analyze_cookies(resp)
    cookie = result["cookies"][0]
    assert cookie["secure"] is False and cookie["http_only"] is False
    assert result["penalty"] > 0
    assert result["findings"]


def test_analyze_cookies_penalty_capped():
    many = [f"c{i}=v" for i in range(20)]
    resp = FakeResponse(set_cookies=many)
    result = server.analyze_cookies(resp)
    assert result["penalty"] <= 24


# --------------------------------------------------------------------------- #
# Technology & WAF/CDN detection
# --------------------------------------------------------------------------- #


def test_detect_technologies():
    html = '<div class="wp-content"><script src="react.js"></script>'
    techs = server.detect_technologies(html)
    assert "WordPress" in techs
    assert "React" in techs
    assert "Laravel" not in techs


def test_detect_waf_cdn():
    headers = {"CF-RAY": "abc123", "Server": "cloudflare"}
    assert "Cloudflare" in server.detect_waf_cdn(headers)
    assert server.detect_waf_cdn({"Server": "nginx"}) == []


# --------------------------------------------------------------------------- #
# Forms & parameter extraction
# --------------------------------------------------------------------------- #


def test_analyze_forms_password_get_is_high():
    html = """
    <form method="get" action="/login">
        <input type="text" name="user">
        <input type="password" name="pass">
    </form>
    """
    soup = BeautifulSoup(html, "html.parser")
    result = server.analyze_forms(soup, "https://example.com")
    assert result["forms"][0]["method"] == "get"
    assert result["penalty"] >= 18
    assert any(f["severity"] == "high" for f in result["findings"])


def test_analyze_forms_post_no_penalty():
    html = '<form method="post" action="/x"><input name="q"></form>'
    soup = BeautifulSoup(html, "html.parser")
    result = server.analyze_forms(soup, "https://example.com")
    assert result["penalty"] == 0
    assert result["findings"] == []


def test_extract_parameter_urls_dedup():
    html = (
        '<a href="/a?x=1">a</a>'
        '<a href="/a?x=1">dup</a>'
        '<a href="/b">no params</a>'
        '<a href="/c?y=2">c</a>'
    )
    soup = BeautifulSoup(html, "html.parser")
    urls = server.extract_parameter_urls(soup, "https://example.com")
    assert urls == ["https://example.com/a?x=1", "https://example.com/c?y=2"]


def test_extract_sitemap_urls():
    xml = """<?xml version="1.0"?>
    <urlset><url><loc>https://example.com/a</loc></url>
    <url><loc>https://example.com/b</loc></url></urlset>"""
    urls = server.extract_sitemap_urls(xml)
    assert urls == ["https://example.com/a", "https://example.com/b"]


# --------------------------------------------------------------------------- #
# TLS findings
# --------------------------------------------------------------------------- #


def test_tls_findings_outdated_protocol():
    result = server.tls_findings({"tls_version": "TLSv1", "days_to_expiry": 300})
    assert result["penalty"] >= 14
    assert any("Outdated" in f["title"] for f in result["findings"])


def test_tls_findings_expired():
    result = server.tls_findings(
        {"tls_version": "TLSv1.3", "expired": True, "valid_until": "old"}
    )
    assert any(f["severity"] == "high" for f in result["findings"])


def test_tls_findings_modern_ok():
    result = server.tls_findings({"tls_version": "TLSv1.3", "days_to_expiry": 200})
    assert result["penalty"] == 0
    assert result["findings"] == []
