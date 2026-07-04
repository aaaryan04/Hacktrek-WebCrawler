import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  FaCode,
  FaFileAlt,
  FaGlobe,
  FaChartLine,
  FaNetworkWired,
  FaRobot,
  FaSearch,
  FaShieldAlt,
  FaSitemap,
  FaWpforms
} from "react-icons/fa";

import "./App.css";

import Footer from "./components/Footer";
import Navbar from "./components/Navbar";
import ResultPanel from "./components/ResultPanel";
import ScanCard from "./components/ScanCard";
import ScanHistory from "./components/ScanHistory";
import SearchBar from "./components/SearchBar";
import StatsCard from "./components/StatsCard";
import ToastStack from "./components/ToastStack";
import { useLocalStorage } from "./hooks/useLocalStorage";
import { useTheme } from "./hooks/useTheme";
import { useToasts } from "./hooks/useToasts";
import { normalizeLogLines } from "./utils/format";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "https://hacktrek-webcrawler.onrender.com";

const HISTORY_KEY = "hacktrek:history";
const HISTORY_LIMIT = 24;

const SCAN_MODULES = [
  {
    endpoint: "assessment",
    title: "Full Assessment",
    description: "Run a complete recon pass with scoring, findings, and recommendations.",
    color: "#facc15",
    icon: FaChartLine
  },
  {
    endpoint: "headers",
    title: "Header Audit",
    description: "Review security headers, server metadata, and response status.",
    color: "#14b8a6",
    icon: FaShieldAlt
  },
  {
    endpoint: "forms",
    title: "Form Mapper",
    description: "Extract forms, actions, methods, and exposed input names.",
    color: "#38bdf8",
    icon: FaWpforms
  },
  {
    endpoint: "tech",
    title: "Tech Fingerprint",
    description: "Detect common frameworks, libraries, and platform signatures.",
    color: "#a78bfa",
    icon: FaCode
  },
  {
    endpoint: "robots",
    title: "Robots Review",
    description: "Fetch robots.txt and inspect crawler rules for hidden paths.",
    color: "#f59e0b",
    icon: FaRobot
  },
  {
    endpoint: "sitemap",
    title: "Sitemap Pull",
    description: "Retrieve sitemap.xml for discoverable routes and content.",
    color: "#f472b6",
    icon: FaSitemap
  },
  {
    endpoint: "subdomains",
    title: "Subdomain Sweep",
    description: "Generate a starter subdomain surface for quick recon.",
    color: "#22c55e",
    icon: FaNetworkWired
  },
  {
    endpoint: "params",
    title: "Parameter Finder",
    description: "Collect URLs that expose query parameters from page links.",
    color: "#06b6d4",
    icon: FaSearch
  }
];

const initialStats = {
  scans: 0,
  score: "--",
  findings: 0,
  headers: 0,
  forms: 0,
  technologies: 0,
  routes: 0
};

function countRoutes(data) {
  if (data?.parameter_urls) {
    return data.parameter_urls.length;
  }

  if (data?.subdomains) {
    return data.subdomains.length;
  }

  if (typeof data?.content === "string") {
    return data.content.split("\n").filter(Boolean).length;
  }

  return 0;
}

function App() {
  const [url, setUrl] = useState("google.com");
  const [activeModule, setActiveModule] = useState("assessment");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [apiStatus, setApiStatus] = useState("checking");
  const [stats, setStats] = useState(initialStats);
  const [liveLogs, setLiveLogs] = useState([]);
  const [streaming, setStreaming] = useState(false);
  const [history, setHistory] = useLocalStorage(HISTORY_KEY, []);
  const [activeHistoryId, setActiveHistoryId] = useState(null);

  const { theme, toggleTheme } = useTheme();
  const { toasts, push: pushToast, dismiss: dismissToast } = useToasts();

  const logTimer = useRef(null);

  const activeScan = useMemo(
    () => SCAN_MODULES.find((module) => module.endpoint === activeModule),
    [activeModule]
  );

  useEffect(() => {
    const controller = new AbortController();

    fetch(`${API_BASE_URL}/`, { signal: controller.signal })
      .then((response) => {
        setApiStatus(response.ok ? "online" : "degraded");
      })
      .catch(() => {
        setApiStatus("offline");
      });

    return () => controller.abort();
  }, []);

  const stopLogPolling = useCallback(() => {
    if (logTimer.current) {
      clearInterval(logTimer.current);
      logTimer.current = null;
    }
    setStreaming(false);
  }, []);

  useEffect(() => stopLogPolling, [stopLogPolling]);

  const startLogPolling = useCallback((target) => {
    // Guard against orphaning a prior interval if a new scan starts while an
    // earlier poll loop is still running (e.g. rapid module re-clicks).
    if (logTimer.current) {
      clearInterval(logTimer.current);
      logTimer.current = null;
    }
    setStreaming(true);

    const poll = async () => {
      try {
        const response = await fetch(
          `${API_BASE_URL}/logs?url=${encodeURIComponent(target)}`
        );
        if (!response.ok) return;
        const data = await response.json();
        const lines = normalizeLogLines(data);
        if (lines.length) {
          setLiveLogs((current) => (lines.length >= current.length ? lines : current));
        }
      } catch {
        // Log endpoint is best-effort; ignore transient failures.
      }
    };

    poll();
    logTimer.current = setInterval(poll, 1100);
  }, []);

  const recordHistory = useCallback(
    (entry) => {
      setHistory((current) => {
        const next = [entry, ...current.filter((item) => item.id !== entry.id)];
        return next.slice(0, HISTORY_LIMIT);
      });
    },
    [setHistory]
  );

  const runScan = useCallback(
    async (endpoint = activeModule) => {
      const target = url.trim();
      const module = SCAN_MODULES.find((item) => item.endpoint === endpoint);

      if (!target) {
        pushToast("Enter a target domain or URL before running a scan.", "error");
        setResult({
          error: "Enter a target domain or URL before running a scan."
        });
        return;
      }

      setActiveModule(endpoint);
      setActiveHistoryId(null);
      setLoading(true);
      setLiveLogs([
        "Initializing recon module",
        `Target queued: ${target}`,
        `Running ${module?.title || endpoint}`
      ]);
      setResult({
        module: module?.title || endpoint,
        target
      });

      startLogPolling(target);

      try {
        const response = await fetch(
          `${API_BASE_URL}/${endpoint}?url=${encodeURIComponent(target)}`
        );
        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || `Request failed with ${response.status}`);
        }

        const enriched = { ...data, module: module?.title || endpoint };
        setResult(enriched);

        const nextScore = data.risk_score ?? null;

        setStats((current) => ({
          scans: current.scans + 1,
          score: data.risk_score ?? current.score,
          findings: data.summary?.findings ?? data.findings?.length ?? current.findings,
          headers:
            data.summary?.headers_present ??
            (data.headers ? Object.keys(data.headers).length : current.headers),
          forms: data.summary?.forms_found ?? data.forms_found ?? current.forms,
          technologies: data.technologies
            ? data.technologies.length
            : current.technologies,
          routes:
            data.summary?.parameterized_urls ||
            data.summary?.sitemap_urls ||
            countRoutes(data) ||
            current.routes
        }));

        const entryId = `${endpoint}-${Date.now()}`;
        recordHistory({
          id: entryId,
          target,
          module: module?.title || endpoint,
          endpoint,
          score: nextScore,
          riskLevel: data.risk_level ?? null,
          timestamp: Date.now(),
          result: enriched
        });
        setActiveHistoryId(entryId);

        pushToast(`${module?.title || endpoint} completed for ${target}`, "success");
      } catch (error) {
        setResult({
          error: error.message,
          module: module?.title || endpoint,
          target
        });
        pushToast(`Scan failed: ${error.message}`, "error");
      } finally {
        setLoading(false);
        stopLogPolling();
      }
    },
    [activeModule, url, pushToast, startLogPolling, stopLogPolling, recordHistory]
  );

  const viewHistoryEntry = useCallback((entry) => {
    setResult(entry.result);
    setActiveModule(entry.endpoint);
    setActiveHistoryId(entry.id);
    setLiveLogs([]);
    if (typeof window !== "undefined") {
      window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
    }
  }, []);

  const clearHistory = useCallback(() => {
    setHistory([]);
    setActiveHistoryId(null);
    pushToast("Scan history cleared", "info");
  }, [setHistory, pushToast]);

  return (
    <div className="page">
      <Navbar apiStatus={apiStatus} theme={theme} onToggleTheme={toggleTheme} />

      <main className="dashboard">
        <section className="hero">
          <div className="hero-copy">
            <p className="eyebrow">Reconnaissance dashboard</p>
            <h1>Hacktrek WebCrawler</h1>
            <p className="subtitle">
              A FastAPI and React reconnaissance platform with risk scoring,
              security findings, technology fingerprinting, and report-ready
              output for authorized website assessments.
            </p>
          </div>

          <div className="hero-panel" aria-label="Project highlights">
            <div>
              <FaGlobe />
              <span>Live target scanning</span>
            </div>
            <div>
              <FaFileAlt />
              <span>Structured JSON results</span>
            </div>
            <div>
              <FaShieldAlt />
              <span>Risk scoring and findings</span>
            </div>
          </div>
        </section>

        <SearchBar
          activeScan={activeScan}
          loading={loading}
          onSearch={() => runScan(activeModule)}
          setUrl={setUrl}
          url={url}
        />

        <section className="modules-section" aria-label="Scanner modules">
          <div className="section-heading">
            <p>Modules</p>
            <h2>Select a scan</h2>
          </div>

          <div className="cards-grid">
            {SCAN_MODULES.map((module) => (
              <ScanCard
                key={module.endpoint}
                active={module.endpoint === activeModule}
                description={module.description}
                icon={module.icon}
                color={module.color}
                onClick={() => runScan(module.endpoint)}
                title={module.title}
              />
            ))}
          </div>
        </section>

        <section className="stats-grid" aria-label="Scan statistics">
          <StatsCard title="Risk Score" value={stats.score} />
          <StatsCard title="Findings" value={stats.findings} />
          <StatsCard title="Scans Run" value={stats.scans} />
          <StatsCard title="Headers Found" value={stats.headers} />
          <StatsCard title="Forms Found" value={stats.forms} />
          <StatsCard title="Tech Matches" value={stats.technologies} />
          <StatsCard title="Routes Found" value={stats.routes} />
        </section>

        <div className="workspace">
          <ResultPanel
            activeScan={activeScan}
            loading={loading}
            result={result}
            liveLogs={liveLogs}
            streaming={streaming}
            notify={pushToast}
          />

          <ScanHistory
            history={history}
            onSelect={viewHistoryEntry}
            onClear={clearHistory}
            activeId={activeHistoryId}
          />
        </div>
      </main>

      <Footer apiBaseUrl={API_BASE_URL} />

      <ToastStack toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}

export default App;
