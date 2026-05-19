function SearchBar({
  url,
  setUrl,
  onSearch
}) {

  return (

    <div className="search-container">

      <input
        type="text"
        placeholder="Enter target URL (e.g., google.com)"
        value={url}
        onChange={(e) =>
          setUrl(e.target.value)
        }
        className="search-input"
      />

      <button
        className="search-button"
        onClick={onSearch}
      >
        →
      </button>

    </div>
  );
}

export default SearchBar;