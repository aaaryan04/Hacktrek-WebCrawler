# 🛡️ Hacktrek WebCrawler

A full-stack reconnaissance and website assessment platform built with **React, Vite, FastAPI, and Python**. It runs authorized recon against a target, fingerprints its exposed surface, scores its security posture, and turns the results into a report-ready export.

> ⚠️ **Educational use only.** Only scan websites you own or have explicit authorization to test.

[![CI](https://github.com/aaaryan04/Hacktrek-WebCrawler/actions/workflows/ci.yml/badge.svg)](https://github.com/aaaryan04/Hacktrek-WebCrawler/actions/workflows/ci.yml)

---

## 🌐 Live Demo

| | |
| --- | --- |
| **Frontend** | [hacktrek-web-crawler.vercel.app](https://hacktrek-web-crawler.vercel.app/) |
| **Backend API** | [hacktrek-webcrawler-s317.onrender.com](https://hacktrek-webcrawler-s317.onrender.com/) |

> The backend is hosted on Render's free tier — the first request after a period of inactivity can take 20-50s to spin the container back up. The dashboard's "API Online/Offline" badge retries automatically once it wakes up.

---

## 📸 Screenshots

> Drop the corresponding image files into `screenshots/` with these exact names and they'll render below.

### Dashboard

![Dashboard](screenshots/dashboard.png)

### Assessment Report

![Assessment Report](screenshots/report.png)

---

## ✨ Features

- 🔍 Full-site assessment workflow with one-click recon across every module
- 📊 Risk scoring engine — score, risk level, severity-ranked findings, and remediation guidance
- 🛡️ HTTP security header audit with missing-header detection
- 🍪 Cookie flag audit (`Secure`, `HttpOnly`, `SameSite`)
- ☁️ WAF / CDN fingerprinting (Cloudflare, Akamai, Fastly, and more)
- 🔐 TLS certificate and protocol inspection with expiry findings
- 🌐 DNS record lookups (A, AAAA, MX, NS, TXT)
- 🚫 DNS-aware SSRF protection — localhost, private, loopback, link-local, and reserved targets are blocked even when reached via DNS or IPv6 rebinding
- 📝 Form discovery with method/input analysis
- 🧩 Technology fingerprinting for common frameworks and libraries
- 🤖 `robots.txt` and `sitemap.xml` collection
- 🔗 Parameterized URL discovery for validation review
- 🌍 Subdomain sweep with live DNS resolution of common candidates
- 📜 Live scan logs streamed into the results panel while a scan runs
- 📚 Scan history persisted to `localStorage`
- 📄 Export to JSON, CSV, or a printable/PDF report, plus copy-to-clipboard
- 🌙 Dark / light theme, persisted and seeded from OS preference
- ⚡ Optional per-IP rate limiting and short-TTL response caching (env-driven)
- ♿ Responsive, accessible dashboard designed for demos and presentations

---

## 🛠️ Scan Modules

| Module | Description |
| --- | --- |
| Full Assessment | Complete recon pass with scoring, findings, and recommendations |
| Header Audit | Review security headers, server metadata, and response status |
| Robots Review | Fetch `robots.txt` and inspect crawler rules for hidden paths |
| Sitemap Pull | Retrieve `sitemap.xml` for discoverable routes and content |
| Form Mapper | Extract forms, actions, methods, and exposed input names |
| Tech Fingerprint | Detect common frameworks, libraries, and platform signatures |
| Parameter Finder | Collect URLs that expose query parameters from page links |
| Subdomain Sweep | Generate and DNS-resolve a starter subdomain surface |
| DNS Lookup | Resolve A, AAAA, MX, NS, and TXT records |
| TLS Inspection | Inspect the SSL/TLS certificate, expiry, and protocol version |

---

## 🏗️ Tech Stack

**Frontend** — React 19 · Vite · CSS · react-icons · Framer Motion

**Backend** — FastAPI · Uvicorn · Requests · BeautifulSoup · dnspython

**DevOps** — Docker · Docker Compose · GitHub Actions CI · pytest

---

## 📁 Project Structure

```text
Hacktrek-WebCrawler/
├── api/            FastAPI routes, scan orchestration, scoring, logging
├── frontend/       React dashboard, assessment report UI, export workflow
├── scanners/       Standalone scanner experiments and CLI modules
├── crawler/        Async/browser crawler experiments
├── database/       Local scan log JSON storage
├── exports/        Sample crawler and scanner output files
├── tests/          Backend test suite (pytest, fully offline)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 🔌 API Reference

All endpoints use `GET`.

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
| `/robots?url=` | Fetches `robots.txt` |
| `/sitemap?url=` | Fetches `sitemap.xml` |
| `/subdomains?url=` | Generates and DNS-resolves common subdomain candidates |
| `/params?url=` | Finds URLs containing query parameters |
| `/tls?url=` (alias `/ssl`) | Inspects the TLS certificate, expiry, and protocol version |
| `/dns?url=` | Resolves A, AAAA, MX, NS, and TXT records |

---

## 📊 Scoring Model

The assessment score starts at 100 and subtracts weighted penalties for issues such as missing security headers, exposed technology banners, risky form methods, parameterized URLs, and error responses.

| Score | Risk |
| ---: | --- |
| 85–100 | 🟢 Low |
| 65–84 | 🟡 Moderate |
| 40–64 | 🟠 High |
| 0–39 | 🔴 Critical |

This is an educational scoring model, not a replacement for a professional penetration test.

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/aaaryan04/Hacktrek-WebCrawler.git
cd Hacktrek-WebCrawler
```

### 2. Install and start the backend

```bash
pip install -r requirements.txt
uvicorn api.server:app --reload
```

### 3. Install and start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

By default, the frontend points at the deployed API above. To use your local backend instead:

```bash
cd frontend
copy .env.example .env.local   # Windows
# cp .env.example .env.local   # macOS / Linux
```

---

## 🧪 Testing

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

---

## 🎬 Demo Flow

1. Start the FastAPI backend and Vite frontend (or use the live demo above).
2. Enter a target you own or have permission to test.
3. Run **Full Assessment**.
4. Walk through the score, findings, technologies, missing headers, and recommendations.
5. Export the JSON/CSV/PDF report as evidence.

---

## 📚 Documentation

- [Project Report](PROJECT_REPORT.md)
- [Security Policy](SECURITY.md)
- [Frontend Notes](frontend/README.md)
- [Contributing](CONTRIBUTING.md)

---

## 🤝 Contributing

Contributions, bug reports, and feature requests are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Open a pull request.

See [CONTRIBUTING.md](CONTRIBUTING.md) for local setup and configuration details.

---

## ⚠️ Responsible Use

Hacktrek WebCrawler is designed for:

- Educational purposes
- Security research
- Authorized penetration testing
- Personal portfolio demonstrations

Do **not** use this project against systems you do not own or do not have explicit permission to test.

---

## 👨‍💻 Author

**Aryan Swarnkar**
Cybersecurity · AI · Ethical Hacking

- GitHub: [@aaaryan04](https://github.com/aaaryan04)

---

### ⭐ Support

If you found this project useful, consider giving it a star on GitHub.
