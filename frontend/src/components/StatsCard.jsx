import { memo } from "react";

import { useCountUp } from "../hooks/useCountUp";

function StatsCard({ title, value, icon: Icon, color }) {
  const display = useCountUp(value);

  return (
    <article className="stats-card" style={color ? { "--stat-color": color } : undefined}>
      {Icon && (
        <span className="stats-icon" aria-hidden="true">
          <Icon />
        </span>
      )}
      <strong>{display}</strong>
      <span>{title}</span>
    </article>
  );
}

export default memo(StatsCard);
