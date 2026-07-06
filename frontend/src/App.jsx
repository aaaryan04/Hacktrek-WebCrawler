import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  FaBolt,
  FaBug,
  FaCode,
  FaFileAlt,
  FaGlobe,
  FaLayerGroup,
  FaChartLine,
  FaNetworkWired,
  FaPlay,
  FaRobot,
  FaSatelliteDish,
  FaSearch,
  FaShieldAlt,
  FaSitemap,
  FaWpforms
} from "react-icons/fa";

import "./App.css";

import Footer from "./components/Footer";
import Logo from "./components/Logo";
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
  import.meta.env.VITE_API_BASE_URL ||
  "https://hacktrek-webcrawler-s317.onrender.com";

const HISTORY_KEY = "hacktrek:history";
const HISTORY_LIMIT = 24;

const SCAN_MODULES = [
  {
    endpoint: "robots",
    title: "Robots Review",
    description: "Fetch robots.txt and inspect crawler rules for hidden paths.",
    color: "#f59e0b",
    icon: FaRobot
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
  },
  {
    endpoint: "assessment",
    title: "Full Assessment",
    description: "Run a complete recon pass with scoring, findings, and recommendations.",
    color: "#facc15",
    icon: FaChartLine
  }
];

const HERO_FEATURES = [
  {
    icon: FaBolt,
    title: "Fast Recon",
    text: "Lightning-fast reconnaissance engine optimized for real-world workflows."
  },
  {
    icon: FaSatelliteDish,
    title: "Deep Intelligence",
    text: "Technology fingerprinting, DNS intelligence, attack surface discovery, and infrastructure analysis."
  },
  {
    icon: FaFileAlt,
    title: "Actionable Results",
    text: "Structured reports, JSON exports, findings, recommendations, and professional reporting."
  }
];

// Right-hero glass cards — mirrors the reference dashboard's capability panel.
const HERO_PANEL_CARDS = [
  {
    icon: FaGlobe,
    title: "Live Target Scanning",
    text: "Real-time reconnaissance and data collection."
  },
  {
    icon: FaFileAlt,
    title: "Structured JSON Results",
    text: "Clean, structured & exportable results format."
  },
  {
    icon: FaShieldAlt,
    title: "Risk Scoring & Findings",
    text: "Intelligent risk analysis with clear actionable insights."
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

const STAT_CARDS = [
  { key: "score", title: "Risk Score", icon: FaShieldAlt, color: "#f43f5e" },
  { key: "findings", title: "Findings", icon: FaBug, color: "#fb923c" },
  { key: "scans", title: "Scans Run", icon: FaPlay, color: "#38bdf8" },
  { key: "headers", title: "Headers Found", icon: FaLayerGroup, color: "#14b8a6" },
  { key: "forms", title: "Forms Found", icon: FaWpforms, color: "#a78bfa" },
  { key: "technologies", title: "Tech Matches", icon: FaCode, color: "#8b5cf6" },
  { key: "routes", title: "Routes Found", icon: FaSitemap, color: "#22c55e" }
];

/** Permissive client-side guard. The backend still performs DNS/SSRF validation. */
function isValidTarget(value) {
  const raw = value.trim();
  if (!raw || /\s/.test(raw)) return false;
  try {
    const url = new URL(/^https?:\/\//i.test(raw) ? raw : `https://${raw}`);
    return url.hostname.includes(".") && url.hostname.length >= 3;
  } catch {
    return false;
  }
}

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
  const [scanningEndpoint, setScanningEndpoint] = useState(null);
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
  // Orchestration refs — the single source of truth for "which scan is current".
  const scanSeqRef = useRef(0); // monotonically increasing id per scan attempt
  const abortRef = useRef(null); // AbortController of the in-flight scan
  const runScanRef = useRef(null); // latest runScan, for the global keyboard shortcut

  const activeScan = useMemo(
    () => SCAN_MODULES.find((module) => module.endpoint === activeModule),
    [activeModule]
  );

  // API health probe — runs once, aborts on unmount. Never triggers a scan.
  useEffect(() => {
    const controller = new AbortController();

    fetch(`${API_BASE_URL}/`, { signal: controller.signal })
      .then((response) => {
        setApiStatus(response.ok ? "online" : "degraded");
      })
      .catch((error) => {
        if (error.name !== "AbortError") setApiStatus("offline");
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

  const startLogPolling = useCallback((target, seq, signal) => {
    // Replace any prior poll loop so only the current scan streams logs.
    if (logTimer.current) {
      clearInterval(logTimer.current);
      logTimer.current = null;
    }
    setStreaming(true);

    const poll = async () => {
      // Bail out the moment this scan is superseded or aborted.
      if (seq !== scanSeqRef.current || signal?.aborted) return;
      try {
        const response = await fetch(
          `${API_BASE_URL}/logs?url=${encodeURIComponent(target)}`,
          { signal }
        );
        if (!response.ok) return;
        const data = await response.json();
        if (seq !== scanSeqRef.current) return;
        const lines = normalizeLogLines(data);
        if (lines.length) {
          setLiveLogs((current) => (lines.length >= current.length ? lines : current));
        }
      } catch {
        // Log endpoint is best-effort; ignore transient/abort failures.
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

  // Selecting a module NEVER scans — it only changes the active target module.
  const selectModule = useCallback((endpoint) => {
    setActiveModule(endpoint);
  }, []);

  const runScan = useCallback(
    async (endpoint = activeModule) => {
      const target = url.trim();
      const module = SCAN_MODULES.find((item) => item.endpoint === endpoint);

      if (!isValidTarget(target)) {
        const message = target
          ? "Enter a valid domain or URL (e.g. example.com)."
          : "Enter a target domain or URL before running a scan.";
        pushToast(message, "error");
        setResult({ error: message });
        return;
      }

      // Supersede any in-flight scan: cancel it and claim a fresh sequence id.
      if (abortRef.current) abortRef.current.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      const seq = scanSeqRef.current + 1;
      scanSeqRef.current = seq;

      setActiveModule(endpoint);
      setScanningEndpoint(endpoint);
      setActiveHistoryId(null);
      setLoading(true);
      setLiveLogs([
        "Initializing recon module",
        `Target queued: ${target}`,
        `Running ${module?.title || endpoint}`
      ]);
      setResult({ module: module?.title || endpoint, target });

      startLogPolling(target, seq, controller.signal);

      try {
        const response = await fetch(
          `${API_BASE_URL}/${endpoint}?url=${encodeURIComponent(target)}`,
          { signal: controller.signal }
        );
        const data = await response.json();

        // A newer scan started while we awaited — drop this stale response.
        if (seq !== scanSeqRef.current) return;

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

        const entryId = `${endpoint}-${seq}`;
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
        // Aborted or superseded scans stay silent — a newer scan owns the UI.
        if (controller.signal.aborted || seq !== scanSeqRef.current) return;
        setResult({ error: error.message, module: module?.title || endpoint, target });
        pushToast(`Scan failed: ${error.message}`, "error");
      } finally {
        // Only the newest scan is allowed to release the shared loading state.
        if (seq === scanSeqRef.current) {
          setLoading(false);
          setScanningEndpoint(null);
          stopLogPolling();
          abortRef.current = null;
        }
      }
    },
    [activeModule, url, pushToast, startLogPolling, stopLogPolling, recordHistory]
  );

  // Keep a ref to the freshest runScan for the global shortcut listener.
  useEffect(() => {
    runScanRef.current = runScan;
  }, [runScan]);

  // Ctrl/Cmd + Enter runs the active scan from anywhere on the page.
  useEffect(() => {
    const onKeyDown = (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        event.preventDefault();
        runScanRef.current?.();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  // Abort any in-flight scan and stop polling when the app unmounts.
  useEffect(
    () => () => {
      if (abortRef.current) abortRef.current.abort();
      if (logTimer.current) clearInterval(logTimer.current);
    },
    []
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

  const handleRun = useCallback(() => runScan(activeModule), [runScan, activeModule]);

  return (
    <div className="page">
      <Navbar apiStatus={apiStatus} theme={theme} onToggleTheme={toggleTheme} />

      <main className="dashboard">
        <motion.section
          className="hero"
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        >
          <div className="hero-copy">
            <p className="eyebrow">Reconnaissance dashboard</p>
            <h1 className="hero-title">
              Hacktrek <span className="accent">WebCrawler</span>
            </h1>

            <p className="hero-tagline">
              <FaShieldAlt aria-hidden="true" />
              <span>Discover. Analyze. Secure.</span>
            </p>

            <p className="subtitle">
              Advanced reconnaissance platform for authorized security
              assessments — fingerprint technologies, surface exposed assets,
              and turn recon data into actionable intelligence.
            </p>

            <div className="hero-features">
              {HERO_FEATURES.map(({ icon: Icon, title, text }) => (
                <div className="hero-feature" key={title} title={text}>
                  <span className="hero-feature-icon">
                    <Icon aria-hidden="true" />
                  </span>
                  <strong>{title}</strong>
                </div>
              ))}
            </div>
          </div>

          <div className="hero-visual">
            <div className="holo" aria-hidden="true">
              <span className="holo-ring holo-ring--1" />
              <span className="holo-ring holo-ring--2" />
              <span className="holo-glow" />
              <Logo size={92} glow className="holo-logo" />
              <span className="holo-base" />
              <span className="holo-particles" />
            </div>

            <ul className="hero-info-cards">
              {HERO_PANEL_CARDS.map(({ icon: Icon, title, text }) => (
                <li className="hero-info-card" key={title}>
                  <span className="hero-info-icon">
                    <Icon aria-hidden="true" />
                  </span>
                  <div>
                    <strong>{title}</strong>
                    <p>{text}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </motion.section>

        <SearchBar
          modules={SCAN_MODULES}
          activeModule={activeModule}
          onSelectModule={selectModule}
          loading={loading}
          onSearch={handleRun}
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
                loading={module.endpoint === scanningEndpoint}
                description={module.description}
                endpoint={module.endpoint}
                icon={module.icon}
                color={module.color}
                onSelect={selectModule}
                title={module.title}
              />
            ))}
          </div>
        </section>

        <section className="stats-grid" aria-label="Scan statistics">
          {STAT_CARDS.map(({ key, title, icon, color }) => (
            <StatsCard
              key={key}
              title={title}
              value={stats[key]}
              icon={icon}
              color={color}
            />
          ))}
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
