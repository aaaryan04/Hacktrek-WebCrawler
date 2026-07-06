import { useCallback, useEffect, useState } from "react";
import { FaCompress, FaExpand } from "react-icons/fa";

import Logo from "./Logo";
import ThemeToggle from "./ThemeToggle";

const STATUS_LABEL = {
  checking: "Checking API",
  online: "API Online",
  degraded: "API Degraded",
  offline: "API Offline"
};

function useFullscreen() {
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    const onChange = () => setIsFullscreen(Boolean(document.fullscreenElement));
    document.addEventListener("fullscreenchange", onChange);
    return () => document.removeEventListener("fullscreenchange", onChange);
  }, []);

  const toggle = useCallback(() => {
    if (document.fullscreenElement) {
      document.exitFullscreen?.();
    } else {
      document.documentElement.requestFullscreen?.().catch(() => {});
    }
  }, []);

  return { isFullscreen, toggle };
}

function Navbar({ apiStatus, theme, onToggleTheme }) {
  const { isFullscreen, toggle } = useFullscreen();
  const statusLabel = STATUS_LABEL[apiStatus] || "API";

  return (
    <header className="navbar">
      <div className="brand">
        <Logo size={46} className="brand-logo" />
        <div className="brand-text">
          <p className="logo">
            Hacktrek <span className="accent">Labs</span>
          </p>
          <p className="logo-sub">Cybersecurity | AI | Ethical Hacking</p>
        </div>
      </div>

      <div className="navbar-actions">
        <div className={`api-badge ${apiStatus}`} title={statusLabel}>
          <span aria-hidden="true" />
          {statusLabel}
        </div>

        <ThemeToggle theme={theme} onToggle={onToggleTheme} />

        <button
          type="button"
          className="icon-button"
          onClick={toggle}
          aria-label={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
          title={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
        >
          {isFullscreen ? <FaCompress aria-hidden="true" /> : <FaExpand aria-hidden="true" />}
        </button>
      </div>
    </header>
  );
}

export default Navbar;
