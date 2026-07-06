import { memo } from "react";

import { SEVERITY_COLORS, SEVERITY_ORDER } from "../utils/format";

/**
 * Inline SVG horizontal bar chart of finding counts by severity.
 */
function SeverityChart({ counts }) {
  const data = SEVERITY_ORDER.map((severity) => ({
    severity,
    count: counts?.[severity] ?? 0
  }));
  const total = data.reduce((sum, item) => sum + item.count, 0);
  const max = Math.max(1, ...data.map((item) => item.count));

  return (
    <div className="severity-chart" aria-label="Findings by severity">
      {total === 0 && <p className="severity-chart-empty">No findings recorded.</p>}
      <ul>
        {data.map(({ severity, count }) => (
          <li key={severity}>
            <span className="severity-chart-label">{severity}</span>
            <span className="severity-chart-track" aria-hidden="true">
              <span
                className="severity-chart-fill"
                style={{
                  width: `${(count / max) * 100}%`,
                  background: SEVERITY_COLORS[severity]
                }}
              />
            </span>
            <span className="severity-chart-value">{count}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default memo(SeverityChart);
