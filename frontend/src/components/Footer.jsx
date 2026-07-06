import { FaLock } from "react-icons/fa";

import Logo from "./Logo";

function Footer({ apiBaseUrl }) {
  return (
    <footer className="footer">
      <div className="footer-brand">
        <Logo size={28} />
        <span>Hacktrek Labs · WebCrawler v2.1</span>
      </div>

      <p className="footer-note">
        <FaLock aria-hidden="true" />
        Built for ethical hackers. Use responsibly and only with authorization.
      </p>

      <div className="footer-meta">
        <span className="footer-api" title={apiBaseUrl}>
          API: {apiBaseUrl}
        </span>
      </div>
    </footer>
  );
}

export default Footer;
