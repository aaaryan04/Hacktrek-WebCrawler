import { useCallback, useEffect, useRef, useState } from "react";

let counter = 0;

/**
 * Minimal toast queue. Each toast auto-dismisses after `duration` ms unless
 * it is dismissed manually first.
 */
export function useToasts() {
  const [toasts, setToasts] = useState([]);
  const timers = useRef(new Map());

  useEffect(() => {
    const timerMap = timers.current;
    return () => {
      timerMap.forEach((timer) => clearTimeout(timer));
      timerMap.clear();
    };
  }, []);

  const dismiss = useCallback((id) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
    const timer = timers.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timers.current.delete(id);
    }
  }, []);

  const push = useCallback(
    (message, tone = "info", duration = 4200) => {
      counter += 1;
      const id = `toast-${counter}`;
      setToasts((current) => [...current, { id, message, tone }]);

      const timer = setTimeout(() => dismiss(id), duration);
      timers.current.set(id, timer);
      return id;
    },
    [dismiss]
  );

  return { toasts, push, dismiss };
}
