import { useCallback, useEffect } from "react";

import { useLocalStorage } from "./useLocalStorage";

const STORAGE_KEY = "hacktrek:theme";

function getInitialTheme() {
  if (typeof window === "undefined") {
    return "dark";
  }

  try {
    // Stored via useLocalStorage → JSON-encoded (e.g. "\"dark\""), so parse it.
    const stored = JSON.parse(window.localStorage.getItem(STORAGE_KEY));
    if (stored === "light" || stored === "dark") {
      return stored;
    }
  } catch {
    // Fall through to system preference.
  }

  const prefersLight =
    window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: light)").matches;

  return prefersLight ? "light" : "dark";
}

/**
 * Theme controller. Persists the choice and reflects it on <html data-theme>
 * so the CSS variable system can swap palettes.
 */
export function useTheme() {
  const [theme, setTheme] = useLocalStorage(STORAGE_KEY, getInitialTheme);

  useEffect(() => {
    const root = document.documentElement;
    root.setAttribute("data-theme", theme);
    root.style.colorScheme = theme;
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme((current) => (current === "dark" ? "light" : "dark"));
  }, [setTheme]);

  return { theme, toggleTheme, setTheme };
}
