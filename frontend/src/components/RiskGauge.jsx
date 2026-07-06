import { memo } from "react";

import { riskLevelClass } from "../utils/format";

const LEVEL_COLORS = {
  low: "#22c55e",
  moderate: "#facc15",
  high: "#f97316",
  critical: "#f43f5e"
};

/**
 * Inline SVG donut gauge for the 0-100 risk score. No chart library needed.
 */
function RiskGauge({ score = 0, level = "" }) {
  const clamped = Math.max(0, Math.min(100, Number(score) || 0));
  const size = 168;
  const stroke = 16;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const dash = (clamped / 100) * circumference;
  const tone = riskLevelClass(level);
  const color = LEVEL_COLORS[tone] || LEVEL_COLORS.low;

  return (
    <div className="risk-gauge">
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        role="img"
        aria-label={`Risk score ${clamped} out of 100, ${level || tone} risk`}
      >
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--gauge-track)"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${dash} ${circumference - dash}`}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: "stroke-dasharray 700ms ease" }}
        />
        <text
          x="50%"
          y="46%"
          textAnchor="middle"
          dominantBaseline="middle"
          className="gauge-score"
          fill="var(--heading)"
        >
          {clamped}
        </text>
        <text
          x="50%"
          y="63%"
          textAnchor="middle"
          dominantBaseline="middle"
          className="gauge-caption"
          fill="var(--text-muted)"
        >
          / 100
        </text>
      </svg>
      <span className={`gauge-level ${tone}`}>{level || tone} risk</span>
    </div>
  );
}

export default memo(RiskGauge);
