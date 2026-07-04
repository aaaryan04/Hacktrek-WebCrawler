function Footer({ apiBaseUrl }) {
  return (
    <footer className="footer">
      <span>Hacktrek WebCrawler v2.0</span>
      <span className="footer-api" title={apiBaseUrl}>
        API: {apiBaseUrl}
      </span>
    </footer>
  );
}

export default Footer;
