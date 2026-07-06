import { useCallback, useEffect, useState } from "react";

/**
 * State synced to localStorage. Falls back gracefully when storage is
 * unavailable (private mode, quota errors) so the UI never crashes.
 *
 * `initialValue` may be a plain value or a lazy `() => value` initializer —
 * the latter is only invoked once, on first mount, like `useState`'s.
 */
export function useLocalStorage(key, initialValue) {
  const resolveInitial = useCallback(
    () => (typeof initialValue === "function" ? initialValue() : initialValue),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  const [value, setValue] = useState(() => {
    if (typeof window === "undefined") {
      return resolveInitial();
    }

    try {
      const stored = window.localStorage.getItem(key);
      return stored !== null ? JSON.parse(stored) : resolveInitial();
    } catch {
      return resolveInitial();
    }
  });

  useEffect(() => {
    try {
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch {
      // Ignore write failures (quota exceeded, disabled storage).
    }
  }, [key, value]);

  const reset = useCallback(() => setValue(resolveInitial()), [resolveInitial]);

  return [value, setValue, reset];
}
