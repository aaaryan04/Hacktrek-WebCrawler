import { memo } from "react";
import { FaSpinner } from "react-icons/fa";

/**
 * A module card. Clicking it ONLY selects the module (sets it as the active
 * scan target) — it never starts a scan. Scans run from the Run Scan button.
 */
function ScanCard({ active, color, description, endpoint, icon: Icon, loading, onSelect, title }) {
  return (
    <button
      className={`scan-card ${active ? "active" : ""} ${loading ? "loading" : ""}`}
      onClick={() => onSelect(endpoint)}
      style={{ "--accent": color }}
      type="button"
      aria-pressed={active}
    >
      <span className="scan-icon">
        {loading ? (
          <FaSpinner className="spin" aria-hidden="true" />
        ) : (
          <Icon aria-hidden="true" />
        )}
      </span>
      <span className="scan-title">{title}</span>
      <span className="scan-description">{description}</span>
      {active && <span className="scan-badge">{loading ? "Scanning" : "Selected"}</span>}
    </button>
  );
}

export default memo(ScanCard);
