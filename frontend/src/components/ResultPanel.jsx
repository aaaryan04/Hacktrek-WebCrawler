import { useState } from "react";
import {
  FaCopy,
  FaFileCsv,
  FaFileCode,
  FaPrint
} from "react-icons/fa";

import RiskGauge from "./RiskGauge";
import SeverityChart from "./SeverityChart";
import ResultSkeleton from "./Skeleton";
import LiveLogs from "./LiveLogs";
import { getSeverityCounts } from "../utils/format";
import {
  copyToClipboard,
  exportCsv,
  exportJson,
  printReport
} from "../utils/exporters";

function getSummary(result) {
  if (!result) {
    return ["Scanner ready", "Choose a module and run a target scan."];
  }

  if (result.error) {
    return ["Scan failed", result.error];
  }

  const summary = [`Module: ${result.module || "Recon scan"}`];

  if (result.url || result.target) {
    summary.push(`Target: ${result.url || result.target}`);
  }

  if (result.risk_score !== undefined) {
    summary.push(`Risk score: ${result.risk_score}/100 (${result.risk_level})`);
  }

  if (result.status_code) {
    summary.push(`HTTP status: ${result.status_code}`);
  }

  if (result.forms_found !== undefined || result.summary?.forms_found !== undefined) {
    summary.push(`Forms found: ${result.forms_found ?? result.summary.forms_found}`);
  }

  if (result.technologies) {
    summary.push(`Technologies: ${result.technologies.length || 0}`);
  }

  if (result.subdomains_found !== undefined) {
    summary.push(`Subdomains: ${result.subdomains_found}`);
  }

  if (result.parameters_found !== undefined || result.summary?.parameterized_urls) {
    summary.push(
      `Parameterized URLs: ${result.parameters_found ?? result.summary.parameterized_urls}`
    );
  }

  return summary;
}

function ReportOverview({ result }) {
  if (result?.risk_score === undefined || result?.risk_score === null) {
    return null;
  }

  const counts = getSeverityCounts(result.findings);

  return (
    <div className="report-overview">
      <div className="gauge-card">
        <RiskGauge score={result.risk_score} level={result.risk_level} />
      </div>

      <div className="overview-chart">
        <h3>Severity distribution</h3>
        <SeverityChart counts={counts} />
      </div>
    </div>
  );
}

function FindingsList({ findings = [] }) {
  if (!findings.length) {
    return <div className="empty-report">No findings returned for this scan.</div>;
  }

  return (
    <div className="findings-list">
      {findings.map((finding, index) => (
        <article className="finding-card" key={`${finding.title}-${index}`}>
          <div>
            <span className={`severity ${finding.severity?.toLowerCase()}`}>
              {finding.severity}
            </span>
            <h3>{finding.title}</h3>
          </div>
          <p>{finding.description}</p>
          <strong>Recommendation</strong>
          <p>{finding.recommendation}</p>
          {finding.evidence && <code>{finding.evidence}</code>}
        </article>
      ))}
    </div>
  );
}

function AssessmentReport({ result }) {
  if (!result || result.error || !result.findings) {
    return null;
  }

  return (
    <div className="assessment-report">
      <ReportOverview result={result} />

      <div className="report-grid">
        <section>
          <h3>Findings ({result.findings.length})</h3>
          <FindingsList findings={result.findings} />
        </section>

        <aside className="report-sidebar">
          <section>
            <h3>Recon Summary</h3>
            <dl>
              <div>
                <dt>Domain</dt>
                <dd>{result.domain}</dd>
              </div>
              <div>
                <dt>Missing Headers</dt>
                <dd>{result.summary?.headers_missing ?? 0}</dd>
              </div>
              <div>
                <dt>Forms</dt>
                <dd>{result.summary?.forms_found ?? 0}</dd>
              </div>
              <div>
                <dt>Sitemap URLs</dt>
                <dd>{result.summary?.sitemap_urls ?? 0}</dd>
              </div>
            </dl>
          </section>

          <section>
            <h3>Technologies</h3>
            <div className="tag-list">
              {result.technologies?.length ? (
                result.technologies.map((technology) => (
                  <span key={technology}>{technology}</span>
                ))
              ) : (
                <span>None detected</span>
              )}
            </div>
          </section>

          <section>
            <h3>Recommendations</h3>
            {result.recommendations?.length ? (
              <ul>
                {result.recommendations.slice(0, 6).map((recommendation) => (
                  <li key={recommendation}>{recommendation}</li>
                ))}
              </ul>
            ) : (
              <p className="sidebar-empty">No recommendations returned.</p>
            )}
          </section>
        </aside>
      </div>
    </div>
  );
}

function ResultPanel({ loading, result, liveLogs, streaming, notify }) {
  const [copied, setCopied] = useState(false);
  const canExport = result && !loading && !result.error;

  const handleCopy = async () => {
    if (!result) return;
    const ok = await copyToClipboard(JSON.stringify(result, null, 2));
    setCopied(ok);
    notify?.(
      ok ? "JSON copied to clipboard" : "Unable to copy JSON",
      ok ? "success" : "error"
    );
    if (ok) {
      setTimeout(() => setCopied(false), 1600);
    }
  };

  const summary = getSummary(result);
  const showLiveLogs = loading || (streaming && liveLogs.length > 0);

  return (
    <section className="result-panel" aria-label="Scan results">
      <div className="result-header">
        <div>
          <p>Output</p>
          <h2>{result?.findings ? "Assessment Report" : "Scan Results"}</h2>
        </div>

        <div className="result-actions">
          <span className={loading ? "status-pill scanning" : "status-pill"}>
            {loading ? "Scanning" : result?.error ? "Needs attention" : "Ready"}
          </span>

          {canExport && (
            <div className="export-group" role="group" aria-label="Export report">
              <button
                className="export-button"
                onClick={() => exportJson(result)}
                type="button"
                title="Download JSON"
              >
                <FaFileCode aria-hidden="true" />
                <span>JSON</span>
              </button>
              <button
                className="export-button"
                onClick={() => exportCsv(result)}
                type="button"
                title="Download CSV"
              >
                <FaFileCsv aria-hidden="true" />
                <span>CSV</span>
              </button>
              <button
                className="export-button"
                onClick={() => printReport(result)}
                type="button"
                title="Open printable report"
              >
                <FaPrint aria-hidden="true" />
                <span>Print</span>
              </button>
              <button
                className="export-button"
                onClick={handleCopy}
                type="button"
                title="Copy JSON to clipboard"
              >
                <FaCopy aria-hidden="true" />
                <span>{copied ? "Copied" : "Copy"}</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {loading ? (
        <ResultSkeleton />
      ) : (
        <AssessmentReport result={result} />
      )}

      <div className="result-layout">
        {showLiveLogs ? (
          <LiveLogs
            lines={liveLogs.length ? liveLogs : summary}
            streaming={loading || streaming}
          />
        ) : (
          <div className="terminal-box">
            {summary.map((line, index) => (
              <p key={`${index}-${line}`}>{line}</p>
            ))}
          </div>
        )}

        <pre>{result ? JSON.stringify(result, null, 2) : "No scan results yet."}</pre>
      </div>
    </section>
  );
}

export default ResultPanel;
