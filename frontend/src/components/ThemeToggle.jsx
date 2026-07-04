import { FaMoon, FaSun } from "react-icons/fa";

function ThemeToggle({ theme, onToggle }) {
  const isDark = theme === "dark";
  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={onToggle}
      aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
      title={isDark ? "Switch to light theme" : "Switch to dark theme"}
    >
      {isDark ? <FaSun aria-hidden="true" /> : <FaMoon aria-hidden="true" />}
      <span>{isDark ? "Light" : "Dark"}</span>
    </button>
  );
}

export default ThemeToggle;
