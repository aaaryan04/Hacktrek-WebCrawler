"""Regression tests for scan-log isolation.

Previously ``/logs`` ignored the ``url`` query param and always returned
whichever scan most recently called ``add_log`` process-wide, so concurrent
scans against different targets could leak each other's log lines. Endpoints
now key their log buffer by the raw target ``url`` string and ``/logs``
looks up that same key.
"""

from api.logger import add_log, clear_logs, get_logs


def test_logs_are_isolated_per_scan_id():
    clear_logs(scan_id="https://target-a.example")
    add_log("[+] scanning target A", scan_id="https://target-a.example")

    clear_logs(scan_id="https://target-b.example")
    add_log("[+] scanning target B", scan_id="https://target-b.example")

    logs_a = get_logs(scan_id="https://target-a.example")
    logs_b = get_logs(scan_id="https://target-b.example")

    assert any("target A" in line for line in logs_a)
    assert not any("target A" in line for line in logs_b)
    assert any("target B" in line for line in logs_b)
    assert not any("target B" in line for line in logs_a)


def test_get_logs_unknown_scan_id_returns_empty():
    assert get_logs(scan_id="https://never-scanned.example") == []


def test_logs_route_scopes_by_url_param(client):
    clear_logs(scan_id="https://route-target.example")
    add_log("[+] route scoped line", scan_id="https://route-target.example")

    scoped = client.get("/logs", params={"url": "https://route-target.example"})
    assert scoped.status_code == 200
    assert any("route scoped line" in line for line in scoped.json()["logs"])

    other = client.get("/logs", params={"url": "https://unrelated.example"})
    assert other.status_code == 200
    assert not any("route scoped line" in line for line in other.json()["logs"])
