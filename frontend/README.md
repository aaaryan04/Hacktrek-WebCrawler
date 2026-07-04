# Hacktrek WebCrawler Frontend

React 19 + Vite dashboard for running Hacktrek WebCrawler scans and viewing
report-ready assessment output. It talks to the FastAPI backend
(`/assessment`, `/headers`, `/forms`, `/tech`, `/robots`, `/sitemap`,
`/subdomains`, `/params`, `/logs`, `/health`).

## Features

- **Eight scan modules** – Full Assessment, Header Audit, Form Mapper, Tech
  Fingerprint, Robots Review, Sitemap Pull, Subdomain Sweep, Parameter Finder.
- **Visual risk gauge** – inline-SVG donut for the 0–100 risk score with a
  colour-coded risk level (no chart library added).
- **Severity distribution chart** – inline-SVG bar chart of findings by
  severity (critical → info).
- **Scan history** – every scan is saved to `localStorage`; click any entry to
  instantly re-view its full result. Clear the list from the history panel.
- **Dark / light theme** – CSS-variable theme system with a toggle in the
  navbar, persisted to `localStorage` and seeded from the OS preference.
- **Report export** – download **JSON**, download **CSV**, open a formatted
  **printable report** (`window.print` → PDF), and **copy JSON** to clipboard.
- **Live logs** – the app polls `GET /logs?url=` during a scan and streams the
  terminal output into the results panel.
- **Toasts, skeletons, and states** – toast notifications for scan
  success/failure, loading skeletons instead of plain text, and clearer
  empty/error states.
- **Accessible + responsive** – keyboard-focus styles, ARIA labelling, and a
  layout that collapses cleanly on tablet and mobile.

## Scripts

```bash
npm install      # install dependencies
npm run dev      # start the dev server
npm run build    # production build
npm run lint     # eslint
npm run preview  # preview the production build
```

## API base URL

The dashboard defaults to the hosted backend. Override it with a Vite env var
when running the backend locally:

```bash
copy .env.example .env.local   # Windows
# cp .env.example .env.local   # macOS / Linux
```

`.env.example`:

```
VITE_API_BASE_URL=http://127.0.0.1:8000
```

`VITE_API_BASE_URL` is read at build time via `import.meta.env`; when it is
unset the app falls back to `https://hacktrek-webcrawler.onrender.com`.

## Project structure

```
src/
  App.jsx              # dashboard shell, scan orchestration, log polling
  components/          # UI: RiskGauge, SeverityChart, ScanHistory, ToastStack,
                       #     ThemeToggle, Skeleton, LiveLogs, ResultPanel, ...
  hooks/               # useLocalStorage, useTheme, useToasts
  utils/               # format helpers + JSON/CSV/print exporters
```
