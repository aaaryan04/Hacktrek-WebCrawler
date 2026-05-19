import { useState } from "react";

import "./App.css";

import Navbar from "./components/Navbar";
import SearchBar from "./components/SearchBar";
import ScanCard from "./components/ScanCard";
import StatsCard from "./components/StatsCard";
import ResultPanel from "./components/ResultPanel";
import Footer from "./components/Footer";

function App() {

  const [url, setUrl] = useState("");

  const [loading, setLoading] = useState(false);

  const [result, setResult] = useState(null);

  const [stats, setStats] = useState({

    scans: 0,
    forms: 0,
    technologies: 0,
    endpoints: 0
  });

  // =========================================
  // RUN SCAN FUNCTION
  // =========================================

  const runScan = async (endpoint) => {

    if (!url) {

      alert("Enter target URL");

      return;
    }

    try {

      setLoading(true);

      setResult({
        logs: [
          "[+] Initializing scan...",
          `[+] Target: ${url}`,
          `[+] Running ${endpoint} module...`
        ]
      });

      const response = await fetch(
        `http://127.0.0.1:8000/${endpoint}?url=${url}`
      );

      const data = await response.json();

      setLoading(false);

      setResult(data);

      setStats({

        scans: stats.scans + 1,

        forms:
          data.forms_found || stats.forms,

        technologies:
          data.technologies
            ? data.technologies.length
            : stats.technologies,

        endpoints:
          data.endpoints
            ? data.endpoints.length
            : stats.endpoints
      });

    } catch (error) {

      setLoading(false);

      setResult({

        error: error.message
      });
    }
  };

  // =========================================
  // UI
  // =========================================

  return (

    <div className="page">

      {/* BACKGROUND EFFECTS */}

      <div className="glow-left"></div>

      <div className="glow-right"></div>

      <div className="grid-overlay"></div>

      {/* NAVBAR */}

      <Navbar />

      {/* MAIN DASHBOARD */}

      <div className="dashboard">

        {/* TITLE */}

        <h1 className="main-title">
          Hacktrek-WebCrawler
        </h1>

        <p className="subtitle">
          Advanced Reconnaissance Framework
        </p>

        <div className="line"></div>

        {/* SEARCH BAR */}

        <SearchBar
          url={url}
          setUrl={setUrl}
          onSearch={() => runScan("headers")}
        />

        {/* SCAN MODULES */}

        <div className="cards-grid">

          <ScanCard
            title="Header Scan"
            description="Analyze HTTP headers"
            color="#00ffbf"
            onClick={() =>
              runScan("headers")
            }
          />

          <ScanCard
            title="Form Extract"
            description="Extract forms & inputs"
            color="#00b7ff"
            onClick={() =>
              runScan("forms")
            }
          />

          <ScanCard
            title="Tech Detect"
            description="Detect technologies"
            color="#bb00ff"
            onClick={() =>
              runScan("tech")
            }
          />

          <ScanCard
            title="robots.txt"
            description="Fetch robots rules"
            color="#ff9900"
            onClick={() =>
              runScan("robots")
            }
          />

          <ScanCard
            title="Sitemap"
            description="Discover sitemap.xml"
            color="#ff00b7"
            onClick={() =>
              runScan("sitemap")
            }
          />

          <ScanCard
            title="Subdomains"
            description="Discover subdomains"
            color="#00ff88"
            onClick={() =>
              runScan("subdomains")
            }
          />

          <ScanCard
            title="URL Params"
            description="Extract URL parameters"
            color="#00ffee"
            onClick={() =>
              runScan("params")
            }
          />

        </div>

        {/* STATS */}

        <div className="stats-grid">

          <StatsCard
            title="SCANS RUN"
            value={stats.scans}
            color="#00ffbf"
          />

          <StatsCard
            title="ENDPOINTS FOUND"
            value={stats.endpoints}
            color="#00b7ff"
          />

          <StatsCard
            title="FORMS FOUND"
            value={stats.forms}
            color="#bb00ff"
          />

          <StatsCard
            title="TECHNOLOGIES"
            value={stats.technologies}
            color="#ff9900"
          />

        </div>

        {/* RESULTS */}

        <ResultPanel
          result={result}
          loading={loading}
        />

        {/* FOOTER */}

        <Footer />

      </div>

    </div>
  );
}

export default App;