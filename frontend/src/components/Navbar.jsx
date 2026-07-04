import ThemeToggle from "./ThemeToggle";

function Navbar({ apiStatus, theme, onToggleTheme }) {
  const statusLabel = {
    checking: "Checking API",
    online: "API Online",
    degraded: "API Degraded",
    offline: "API Offline"
  }[apiStatus];

  return (
    <header className="navbar">
      <div className="brand">
        <span className="brand-mark">HT</span>
        <div>
          <p className="logo">Hacktrek</p>
          <p className="logo-sub">WebCrawler</p>
        </div>
      </div>

      <div className="navbar-actions">
        <div className={`api-badge ${apiStatus}`}>
          <span aria-hidden="true"></span>
          {statusLabel}
        </div>
        <ThemeToggle theme={theme} onToggle={onToggleTheme} />
      </div>
    </header>
  );
}

export default Navbar;
