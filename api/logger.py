"""Thread-safe, in-memory scan logger.

The previous implementation wrote every log line to a single shared JSON file
(``database/scan_logs.json``) and truncated it at the start of *every* request.
Under any concurrency that turned ``/logs`` into a race condition and made the
returned lines meaningless.

This module keeps logs entirely in memory and isolates each request using a
``contextvars`` scan id, so concurrent scans never overwrite one another. A
bounded ring buffer keeps memory usage flat. The public helpers
``clear_logs()`` / ``add_log()`` / ``get_logs()`` keep the exact same call
signatures the API already relies on.
"""

import contextvars
import threading
import time
from collections import OrderedDict, deque

# --------------------------------------------------------------------------- #
# Internal state (all access guarded by _LOCK)
# --------------------------------------------------------------------------- #

_LOCK = threading.RLock()

_MAX_SCANS = 50          # how many distinct scans to retain
_MAX_LINES_PER_SCAN = 500  # ring-buffer size per scan

# scan_id -> deque[str]
_scans: "OrderedDict[str, deque]" = OrderedDict()

# id of the most recently active scan (what bare /logs returns)
_latest_scan_id = None

# per-request scan id, isolates concurrent requests (thread + async safe)
_current_scan: "contextvars.ContextVar[str | None]" = contextvars.ContextVar(
    "current_scan_id", default=None
)


def _timestamp() -> str:
    return time.strftime("%H:%M:%S")


def start_scan(scan_id: str | None = None) -> str:
    """Begin a fresh scan for the current request context and return its id."""
    global _latest_scan_id

    if scan_id is None:
        scan_id = f"scan-{int(time.time() * 1000)}-{threading.get_ident()}"

    with _LOCK:
        _scans[scan_id] = deque(maxlen=_MAX_LINES_PER_SCAN)
        _scans.move_to_end(scan_id)
        _latest_scan_id = scan_id
        while len(_scans) > _MAX_SCANS:
            _scans.popitem(last=False)

    _current_scan.set(scan_id)
    return scan_id


def clear_logs(scan_id: str | None = None) -> str:
    """Start a fresh log buffer for this request.

    Kept for backwards compatibility: endpoints historically called
    ``clear_logs()`` at the top of the handler. It now simply begins a new,
    context-isolated scan instead of truncating a globally shared file.
    """
    return start_scan(scan_id)


def add_log(message: str, scan_id: str | None = None) -> str:
    """Append a timestamped line to the current (or given) scan."""
    global _latest_scan_id

    line = f"[{_timestamp()}] {message}"
    sid = scan_id or _current_scan.get()

    with _LOCK:
        if sid is None or sid not in _scans:
            sid = start_scan(sid)
        _scans[sid].append(line)
        _latest_scan_id = sid

    return line


def get_logs(scan_id: str | None = None) -> list:
    """Return log lines for the given scan, or the most recent scan."""
    with _LOCK:
        if scan_id is not None:
            return list(_scans.get(scan_id, ()))
        current = _current_scan.get()
        if current is not None and current in _scans:
            return list(_scans[current])
        if _latest_scan_id is not None and _latest_scan_id in _scans:
            return list(_scans[_latest_scan_id])
        return []
