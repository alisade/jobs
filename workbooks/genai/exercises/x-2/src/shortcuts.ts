// Production shortcut registry: window keydown listeners. Combos look like "alt+h".
import type { Shortcuts } from "./types";

function matches(e: KeyboardEvent, combo: string): boolean {
  const parts = combo.toLowerCase().split("+");
  const key = parts[parts.length - 1];
  return (
    e.key.toLowerCase() === key &&
    e.altKey === parts.includes("alt") &&
    e.ctrlKey === parts.includes("ctrl") &&
    e.shiftKey === parts.includes("shift")
  );
}

export const windowShortcuts: Shortcuts = {
  register(combo, fn) {
    const onKey = (e: KeyboardEvent) => {
      if (matches(e, combo)) {
        e.preventDefault();
        fn();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  },
};
