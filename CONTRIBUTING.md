# Contributing to Hacktrek WebCrawler

Thanks for helping improve Hacktrek WebCrawler! This guide covers local setup,
testing, and the conventions used across the backend and frontend.

> **Responsible use:** only scan systems you own, manage, or have explicit
> written permission to test. See [SECURITY.md](SECURITY.md).

## Project layout

```text
api/          FastAPI app (server.py), logging, rate limiting, caching
frontend/     React + Vite dashboard
tests/        Offline pytest suite for the backend
.github/      CI workflows
```

## Prerequisites

- Python 3.12+ (3.13 recommended)
- Node.js 20+
- Optional: Docker + Docker Compose

## Backend setup

```bash
python -m venv venv
# Windows: venv\Scripts\activate     macOS/Linux: source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

Run the API with reload:

```bash
uvicorn api.server:app --reload
# or: make run-api
```

### Configuration

All backend configuration is environment-driven. Copy `.env.example` to `.env`
and edit as needed:

| Variable | Default | Purpose |
| --- | --- | --- |
| `ALLOWED_ORIGINS` | localhost dev origins | Comma-separated CORS allow-list |
| `ALLOWED_ORIGIN_REGEX` | matches `hacktrek-web-crawler*.vercel.app` | Regex CORS allow-list (covers Vercel preview URLs) |
| `ALLOW_CREDENTIALS` | `false` | Allow credentialed CORS (ignored with `*`) |
| `REQUEST_TIMEOUT` | `10` | Seconds before an outbound fetch times out |
| `USER_AGENT` | `Hacktrek-WebCrawler/2.0` | UA sent on scan requests |
| `MAX_REDIRECTS` | `10` | Max redirects followed |
| `DNS_NAMESERVERS` | `8.8.8.8,1.1.1.1` | Resolvers (`system` = OS resolvers) |
| `DNS_TIMEOUT` | `5` | Seconds budget for DNS queries |
| `TLS_TIMEOUT` | `6` | Seconds budget for the TLS handshake |
| `RATE_LIMIT_PER_MINUTE` | `0` | Per-IP requests/min; `0` disables limiting |
| `SCAN_CACHE_TTL` | `0` | TTL (s) for cached scan results; `0` disables |

## Frontend setup

```bash
cd frontend
npm ci
npm run dev     # dev server
npm run lint    # eslint
npm run build   # production build
```

To point the dashboard at a local backend, copy `frontend/.env.example` to
`frontend/.env.local` and set `VITE_API_BASE_URL=http://127.0.0.1:8000`.

## Testing

The backend suite runs **fully offline** — all outbound HTTP, DNS, and TLS calls
are mocked. Never add tests that reach the network.

```bash
pytest -q
# or: make test
```

Please add or update tests for any backend change. Good targets:

- New endpoints → add a `TestClient` test (see `tests/test_basic_routes.py`).
- New analysis helpers → unit-test the pure function directly.
- Validation / SSRF rules → extend `tests/test_validation_ssrf.py`.

## Rate limiting & caching

- `api/rate_limit.py` provides a per-IP sliding-window `RateLimitMiddleware`,
  wired into the app and controlled by `RATE_LIMIT_PER_MINUTE` (0 = off).
- `api/cache.py` provides a `TTLCache` and `@ttl_cache` decorator for GET scan
  endpoints, controlled by `SCAN_CACHE_TTL` (0 = off). It is ready to apply to
  handlers when short-lived result caching is desired.

## Docker

```bash
make docker-build          # build the backend image
docker compose up --build  # run the API on :8000
docker compose --profile frontend up   # also serve built frontend on :8080
```

## Coding conventions

- **Python:** keep endpoints thin; put reusable logic in shared helpers. Match
  the existing style in `api/server.py`. Prefer explicit `HTTPException`s with
  correct status codes.
- **JavaScript/React:** code must pass `npm run lint` and `npm run build`.
- Keep changes focused and covered by tests. CI (`.github/workflows/ci.yml`)
  must be green: backend `pytest` and frontend `lint` + `build`.

## Pull requests

1. Create a feature branch.
2. Make your change with tests.
3. Ensure `pytest -q`, `npm run lint`, and `npm run build` all pass.
4. Open a PR describing the change and its motivation.
