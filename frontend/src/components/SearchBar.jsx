import { FaChevronDown, FaPlay, FaSpinner } from "react-icons/fa";

/**
 * Target bar. The module dropdown ONLY changes the selected module — it never
 * launches a scan. Scanning happens exclusively via the Run Scan button, the
 * Enter key inside the input, or the global Ctrl/Cmd+Enter shortcut.
 */
function SearchBar({
  modules,
  activeModule,
  onSelectModule,
  loading,
  onSearch,
  setUrl,
  url
}) {
  return (
    <section className="search-container" aria-label="Target scanner">
      <label className="search-select" htmlFor="module-select">
        <span>Target</span>
        <div className="search-select-control">
          <select
            id="module-select"
            value={activeModule}
            onChange={(event) => onSelectModule(event.target.value)}
            disabled={loading}
          >
            {modules.map((module) => (
              <option key={module.endpoint} value={module.endpoint}>
                {module.title}
              </option>
            ))}
          </select>
          <FaChevronDown aria-hidden="true" />
        </div>
      </label>

      <input
        aria-label="Target URL"
        className="search-input"
        onChange={(event) => setUrl(event.target.value)}
        onKeyDown={(event) => {
          if (event.key !== "Enter") return;
          event.preventDefault();
          // Ctrl/Cmd+Enter is owned exclusively by the global window-level
          // shortcut (App.jsx) — bail here so a single keypress can't fire
          // runScan twice (once from this handler, once from that listener).
          if (event.ctrlKey || event.metaKey) return;
          onSearch();
        }}
        placeholder="Enter a target site, e.g. example.com"
        type="text"
        autoComplete="off"
        autoCapitalize="off"
        autoCorrect="off"
        spellCheck="false"
        value={url}
      />

      <button
        className="search-button"
        disabled={loading}
        onClick={onSearch}
        type="button"
        title="Run scan (Ctrl + Enter)"
      >
        {loading ? (
          <FaSpinner className="spin" aria-hidden="true" />
        ) : (
          <FaPlay aria-hidden="true" />
        )}
        <span>{loading ? "Scanning" : "Run Scan"}</span>
      </button>
    </section>
  );
}

export default SearchBar;
