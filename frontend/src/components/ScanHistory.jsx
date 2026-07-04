import { FaHistory, FaTrashAlt } from "react-icons/fa";

import { formatTimestamp, riskLevelClass } from "../utils/format";

function ScanHistory({ history, onSelect, onClear, activeId }) {
  return (
    <section className="history-panel" aria-label="Scan history">
      <div className="history-header">
        <div className="history-title">
          <FaHistory aria-hidden="true" />
          <div>
            <p>History</p>
            <h2>Recent scans</h2>
          </div>
        </div>
        {history.length > 0 && (
          <button type="button" className="ghost-button" onClick={onClear}>
            <FaTrashAlt aria-hidden="true" />
            <span>Clear</span>
          </button>
        )}
      </div>

      {history.length === 0 ? (
        <p className="history-empty">
          Past scans are saved to your browser and appear here. Run a scan to begin.
        </p>
      ) : (
        <ul className="history-list">
          {history.map((entry) => (
            <li key={entry.id}>
              <button
                type="button"
                className={`history-item ${entry.id === activeId ? "active" : ""}`}
                onClick={() => onSelect(entry)}
              >
                <span className="history-item-main">
                  <span className="history-item-target">{entry.target}</span>
                  <span className="history-item-module">{entry.module}</span>
                </span>
                <span className="history-item-meta">
                  {entry.score !== null && entry.score !== undefined && (
                    <span className={`history-score ${riskLevelClass(entry.riskLevel)}`}>
                      {entry.score}
                    </span>
                  )}
                  <span className="history-time">{formatTimestamp(entry.timestamp)}</span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default ScanHistory;
