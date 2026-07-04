# Hacktrek WebCrawler

Hacktrek WebCrawler is a full-stack reconnaissance and website assessment dashboard built with React, Vite, FastAPI, and Python. It helps run quick authorized checks against a target website, summarize the exposed surface, score basic security posture, and export structured evidence for reporting.

## Final Project Scope

This project is designed as a practical cybersecurity and web engineering final project. It combines a modern dashboard, API-driven scanner modules, risk scoring, evidence collection, and report-ready output.

## Key Features

- Full assessment workflow with one-click recon across multiple modules
- Security score, risk level, severity findings, and remediation guidance
- DNS-aware SSRF protection: localhost, private, loopback, link-local, and
  reserved targets are blocked even when reached via DNS or IPv6 translation
- HTTP security header audit with missing-header detection
- Cookie flag audit (Secure, HttpOnly, SameSite)
- WAF / CDN fingerprinting (Cloudflare, Akamai, Fastly, and more)
- TLS certificate and protocol inspection with expiry findings
- DNS record lookups (A, AAAA, MX, NS, TXT)
- Form discovery with method/input analysis
- Technology fingerprinting for common frameworks and libraries
- robots.txt and sitemap.xml collection
- Parameterized URL discovery for validation review
- Subdomain sweep with live DNS resolution of common candidates
- Exportable JSON, CSV, and printable/PDF reports plus copy-to-clipboard
- Optional per-IP rate limiting and short-TTL response caching (env-driven)
- Responsive dashboard designed for demos, screenshots, and presentations

## Documentation

- [Project Report](PROJECT_REPORT.md)
- [Security Policy](SECURITY.md)
- [Frontend Notes](frontend/README.md)

## Tech Stack

- Frontend: React 19, Vite, CSS, react-icons
- Backend: FastAPI, Uvicorn, Requests, BeautifulSoup, dnspython
- Testing / DevOps: pytest, Docker, docker-compose, GitHub Actions CI
- Language: JavaScript and Python
- Output: Structured JSON assessment reports (plus CSV and printable exports)

## Architecture

```text
frontend/     React dashboard, assessment report UI, export workflow
api/          FastAPI routes, scan orchestration, scoring, logging
scanners/     Standalone scanner experiments and CLI modules
crawler/      Async/browser crawler experiments
database/     Local scan log JSON storage
exports/      Sample crawler and scanner output files
```

## API Modules

| Endpoint | Purpose |
| --- | --- |
| `/` | Root info: API version and available modules |
| `/health` | Health check (includes DNS availability) for monitoring |
| `/modules` | Lists available scanner modules |
| `/logs` | Returns the most recent scan's live log lines (polled by the UI) |
| `/assessment?url=` | Runs a complete assessment with scoring, cookies, WAF/CDN, and TLS |
| `/headers?url=` | Collects HTTP response headers, cookie flags, and WAF/CDN hints |
| `/forms?url=` | Extracts forms and input fields |
| `/tech?url=` | Detects common technology signatures |
| `/robots?url=` | Fetches robots.txt |
| `/sitemap?url=` | Fetches sitemap.xml |
| `/subdomains?url=` | Generates and DNS-resolves common subdomain candidates |
| `/params?url=` | Finds URLs containing query parameters |
| `/tls?url=` (alias `/ssl`) | Inspects the TLS certificate, expiry, and protocol version |
| `/dns?url=` | Resolves A, AAAA, MX, NS, and TXT records |

All endpoints use the `GET` method. Deployment (Docker, docker-compose) and a
GitHub Actions CI workflow are included; see `Dockerfile`, `docker-compose.yml`,
and `.github/workflows/ci.yml`.

## Scoring Model

The assessment score starts at 100 and subtracts weighted penalties for issues such as missing security headers, exposed technology banners, risky form methods, parameterized URLs, and error responses. The result is mapped into:

- Low risk: 85-100
- Moderate risk: 65-84
- High risk: 40-64
- Critical risk: 0-39

This is an educational scoring model, not a replacement for a professional penetration test.

## Run Locally

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn api.server:app --reload
```

Install and start the frontend:

```bash
cd frontend
npm install
npm run dev
```

By default, the frontend uses the deployed API URL. To use your local backend, copy the example environment file:

```bash
cd frontend
copy .env.example .env.local
```

## Testing

Backend tests run fully offline (no network calls):

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
```

Frontend checks:

```bash
cd frontend
npm run lint
npm run build
```

## Demo Flow

1. Start the FastAPI backend and Vite frontend.
2. Enter a target you own or have permission to test.
3. Run `Full Assessment`.
4. Walk through the score, findings, technologies, missing headers, and recommendations.
5. Export the JSON report as evidence.

## Before Publishing on GitHub

Recommended cleanup before your first public push:

```bash
git rm -r --cached node_modules frontend/node_modules venv api/__pycache__
git rm --cached database/scan_logs.json
git add .
git commit -m "Prepare Hacktrek WebCrawler for public release"
```

This keeps dependencies, virtual environments, runtime logs, and bytecode caches out of the public repository while preserving them locally.

## Responsible Use

Use Hacktrek WebCrawler only on websites you own, manage, or have explicit permission to test. The project is intended for education, portfolio demonstration, and authorized reconnaissance.
