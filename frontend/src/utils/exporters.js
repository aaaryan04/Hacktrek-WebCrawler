import { getSeverityCounts } from "./format";

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  // Defer revocation — some browsers read the blob URL asynchronously after
  // the click, and revoking it synchronously can abort the download.
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

function safeName(result) {
  return (result?.domain || result?.target || result?.url || "scan")
    .replace(/^https?:\/\//, "")
    .replace(/[^a-z0-9.-]/gi, "-")
    .replace(/-+/g, "-")
    .toLowerCase();
}

export function exportJson(result) {
  if (!result) return;
  const blob = new Blob([JSON.stringify(result, null, 2)], {
    type: "application/json"
  });
  triggerDownload(blob, `hacktrek-${safeName(result)}-report.json`);
}

function csvCell(value) {
  let text = value === null || value === undefined ? "" : String(value);
  // Scan results can embed attacker-controlled strings from the target site
  // (header values, form field names, evidence...). A leading =/+/-/@ would
  // be interpreted as a formula by Excel/Sheets — neutralize it.
  if (/^[=+\-@]/.test(text)) {
    text = `'${text}`;
  }
  if (/[",\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

export function exportCsv(result) {
  if (!result) return;

  const rows = [["Section", "Key", "Value"]];

  rows.push(["Meta", "Module", result.module || ""]);
  rows.push(["Meta", "Target", result.url || result.target || result.domain || ""]);

  if (result.risk_score !== undefined) {
    rows.push(["Risk", "Score", `${result.risk_score}/100`]);
    rows.push(["Risk", "Level", result.risk_level || ""]);
  }

  const counts = getSeverityCounts(result.findings);
  Object.entries(counts).forEach(([severity, count]) => {
    rows.push(["Severity", severity, count]);
  });

  (result.findings || []).forEach((finding, index) => {
    const prefix = `Finding ${index + 1}`;
    rows.push([prefix, "Title", finding.title]);
    rows.push([prefix, "Severity", finding.severity]);
    rows.push([prefix, "Description", finding.description]);
    rows.push([prefix, "Recommendation", finding.recommendation]);
    if (finding.evidence) {
      rows.push([prefix, "Evidence", finding.evidence]);
    }
  });

  (result.technologies || []).forEach((tech) => {
    rows.push(["Technology", "Detected", tech]);
  });

  (result.recommendations || []).forEach((rec, index) => {
    rows.push(["Recommendation", `#${index + 1}`, rec]);
  });

  const csv = rows.map((row) => row.map(csvCell).join(",")).join("\r\n");
  // Prepend a UTF-8 BOM () so spreadsheet apps detect encoding correctly.
  const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
  triggerDownload(blob, `hacktrek-${safeName(result)}-report.csv`);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export function printReport(result) {
  if (!result) return;

  const target = escapeHtml(result.url || result.target || result.domain || "target");
  const counts = getSeverityCounts(result.findings);
  const generated = new Date().toLocaleString();

  const severityRows = Object.entries(counts)
    .map(
      ([severity, count]) =>
        `<tr><td style="text-transform:capitalize">${severity}</td><td>${count}</td></tr>`
    )
    .join("");

  const findingsHtml = (result.findings || [])
    .map(
      (finding) => `
        <article class="finding">
          <span class="tag ${escapeHtml((finding.severity || "").toLowerCase())}">${escapeHtml(finding.severity)}</span>
          <h3>${escapeHtml(finding.title)}</h3>
          <p>${escapeHtml(finding.description)}</p>
          <p><strong>Recommendation:</strong> ${escapeHtml(finding.recommendation)}</p>
          ${finding.evidence ? `<pre>${escapeHtml(finding.evidence)}</pre>` : ""}
        </article>`
    )
    .join("");

  const recHtml = (result.recommendations || [])
    .map((rec) => `<li>${escapeHtml(rec)}</li>`)
    .join("");

  const techHtml = (result.technologies || [])
    .map((tech) => `<span class="chip">${escapeHtml(tech)}</span>`)
    .join(" ");

  const html = `<!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <title>Hacktrek Report - ${target}</title>
        <style>
          * { box-sizing: border-box; }
          body { font-family: Arial, Helvetica, sans-serif; color: #0f172a; margin: 32px; }
          h1 { margin: 0 0 4px; }
          .muted { color: #64748b; }
          .score { font-size: 48px; font-weight: 800; }
          table { border-collapse: collapse; margin: 12px 0; width: 260px; }
          td { border: 1px solid #cbd5e1; padding: 6px 10px; }
          .finding { border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px 16px; margin: 12px 0; page-break-inside: avoid; }
          .tag { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px; font-weight: 700; text-transform: uppercase; background: #e2e8f0; }
          .tag.high, .tag.critical { background: #fee2e2; color: #b91c1c; }
          .tag.medium { background: #fef3c7; color: #92400e; }
          .tag.low { background: #e0f2fe; color: #075985; }
          .chip { display: inline-block; padding: 3px 10px; border-radius: 999px; background: #ccfbf1; color: #0f766e; font-size: 13px; margin: 2px; }
          pre { background: #0f172a; color: #99f6e4; padding: 10px; border-radius: 6px; overflow-wrap: anywhere; white-space: pre-wrap; }
          @media print { body { margin: 12mm; } }
        </style>
      </head>
      <body>
        <h1>Hacktrek WebCrawler Report</h1>
        <p class="muted">Target: ${target} &middot; Generated ${escapeHtml(generated)}</p>
        ${
          result.risk_score !== undefined
            ? `<p class="score">${escapeHtml(result.risk_score)}<span class="muted" style="font-size:18px">/100 &middot; ${escapeHtml(result.risk_level || "")} risk</span></p>`
            : ""
        }
        <h2>Severity distribution</h2>
        <table><tbody>${severityRows}</tbody></table>
        ${techHtml ? `<h2>Technologies</h2><p>${techHtml}</p>` : ""}
        <h2>Findings</h2>
        ${findingsHtml || "<p class='muted'>No findings recorded.</p>"}
        ${recHtml ? `<h2>Recommendations</h2><ul>${recHtml}</ul>` : ""}
      </body>
    </html>`;

  const printWindow = window.open("", "_blank", "width=900,height=1000");
  if (!printWindow) return;
  printWindow.document.open();
  printWindow.document.write(html);
  printWindow.document.close();
  printWindow.focus();
  setTimeout(() => printWindow.print(), 350);
}

export async function copyToClipboard(text) {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    // Fall through to legacy path.
  }

  try {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    const ok = document.execCommand("copy");
    textarea.remove();
    return ok;
  } catch {
    return false;
  }
}
