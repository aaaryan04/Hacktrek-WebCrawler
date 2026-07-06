import { useEffect, useRef, useState } from "react";

/**
 * Smoothly animates a numeric value from its previous value to the next one.
 * Non-numeric values (e.g. the "--" placeholder) are passed straight through.
 * Respects prefers-reduced-motion by snapping instantly.
 */
export function useCountUp(value, duration = 700) {
  const numeric = typeof value === "number" && Number.isFinite(value);
  const [display, setDisplay] = useState(numeric ? value : 0);
  const fromRef = useRef(numeric ? value : 0);
  const rafRef = useRef(null);

  useEffect(() => {
    if (!numeric) return undefined;

    const reduce =
      typeof window !== "undefined" &&
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const from = fromRef.current;
    const to = value;

    if (reduce || from === to) {
      setDisplay(to);
      fromRef.current = to;
      return undefined;
    }

    let start = null;
    const step = (timestamp) => {
      if (start === null) start = timestamp;
      const progress = Math.min((timestamp - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
      setDisplay(Math.round(from + (to - from) * eased));
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(step);
      } else {
        fromRef.current = to;
      }
    };

    rafRef.current = requestAnimationFrame(step);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [value, duration, numeric]);

  return numeric ? display : value;
}
