"""Smoke tests for the always-available informational routes."""


def test_home(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "Hacktrek WebCrawler API running"
    assert "version" in body
    assert isinstance(body["modules"], list)
    assert "assessment" in body["modules"]


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "Hacktrek WebCrawler API"
    assert "dns_available" in body


def test_modules(client):
    resp = client.get("/modules")
    assert resp.status_code == 200
    modules = resp.json()["modules"]
    assert isinstance(modules, list) and modules
    endpoints = {m["endpoint"] for m in modules}
    assert {"assessment", "headers", "tls", "dns"}.issubset(endpoints)
    for m in modules:
        assert {"endpoint", "name", "description"} <= m.keys()


def test_logs_route_shape(client):
    resp = client.get("/logs")
    assert resp.status_code == 200
    assert "logs" in resp.json()
