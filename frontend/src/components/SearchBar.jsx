import { FaPlay } from "react-icons/fa";

function SearchBar({ activeScan, loading, onSearch, setUrl, url }) {
  return (
    <section className="search-container" aria-label="Target scanner">
      <div className="search-copy">
        <span>Target</span>
        <strong>{activeScan?.title || "Scanner"}</strong>
      </div>

      <input
        aria-label="Target URL"
        className="search-input"
        onChange={(event) => setUrl(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter") {
            onSearch();
          }
        }}
        placeholder="example.com or https://example.com"
        type="text"
        value={url}
      />

      <button className="search-button" disabled={loading} onClick={onSearch}>
        <FaPlay aria-hidden="true" />
        <span>{loading ? "Scanning" : "Run Scan"}</span>
      </button>
    </section>
  );
}

export default SearchBar;
