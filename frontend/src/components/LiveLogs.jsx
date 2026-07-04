import { useEffect, useRef } from "react";

/**
 * Terminal-style live log viewer. Auto-scrolls to the newest line.
 */
function LiveLogs({ lines = [], streaming = false }) {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, [lines]);

  return (
    <div className="terminal-box" aria-label="Live scan logs" aria-live="polite">
      {lines.length === 0 ? (
        <p>Waiting for log output...</p>
      ) : (
        lines.map((line, index) => <p key={`${index}-${line}`}>{line}</p>)
      )}
      {streaming && <p className="terminal-cursor">streaming logs</p>}
      <span ref={endRef} />
    </div>
  );
}

export default LiveLogs;
