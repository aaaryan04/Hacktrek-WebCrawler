import { useCallback, useEffect, useState } from "react";

/**
 * State synced to localStorage. Falls back gracefully when storage is
 * unavailable (private mode, quota errors) so the UI never crashes.
 */
export function useLocalStorage(key, initialValue) {
  const [value, setValue] = useState(() => {
    if (typeof window === "undefined") {
      return initialValue;
    }

    try {
      const stored = window.localStorage.getItem(key);
      return stored !== null ? JSON.parse(stored) : initialValue;
    } catch {
      return initialValue;
    }
  });

  useEffect(() => {
    try {
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch {
      // Ignore write failures (quota exceeded, disabled storage).
    }
  }, [key, value]);

  const reset = useCallback(() => setValue(initialValue), [initialValue]);

  return [value, setValue, reset];
}
