import { memo, useId } from "react";

/**
 * Official Hacktrek Labs mark — a security shield enclosing a terminal prompt
 * (>_). Rendered as a crisp, theme-aware SVG so it stays sharp at any size and
 * can glow for the hero centerpiece. Every instance gets unique gradient ids
 * (useId) so multiple logos on one page never collide.
 */
function Logo({ size = 44, glow = false, title = "Hacktrek Labs", className = "" }) {
  const uid = useId().replace(/:/g, "");
  const strokeId = `htk-stroke-${uid}`;
  const glowId = `htk-glow-${uid}`;

  return (
    <svg
      className={`htk-logo ${glow ? "htk-logo--glow" : ""} ${className}`}
      width={size}
      height={size}
      viewBox="0 0 64 64"
      role="img"
      aria-label={title}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <title>{title}</title>
      <defs>
        <linearGradient id={strokeId} x1="12" y1="4" x2="52" y2="60" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#67e8f9" />
          <stop offset="0.5" stopColor="#22d3ee" />
          <stop offset="1" stopColor="#0891b2" />
        </linearGradient>
        {glow && (
          <filter id={glowId} x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation="2.4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        )}
      </defs>

      <g
        stroke={`url(#${strokeId})`}
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
        filter={glow ? `url(#${glowId})` : undefined}
      >
        {/* Shield silhouette */}
        <path d="M32 5 L55 13 V30 C55 44.5 45.5 54.5 32 59.5 C18.5 54.5 9 44.5 9 30 V13 Z" />
        {/* Terminal chevron ">" */}
        <path d="M23 26 L31 33 L23 40" />
        {/* Terminal underscore "_" */}
        <line x1="34" y1="41" x2="44" y2="41" />
      </g>
    </svg>
  );
}

export default memo(Logo);
