// Turns assistant gateway events into the answer the panel renders.
import type { SseEvent } from "./sse";

export interface Transcript {
  text: string;
  done: boolean;
  conversationId?: string;
}

export const empty: Transcript = { text: "", done: false };

function json(data: string): Record<string, unknown> | undefined {
  try {
    const v = JSON.parse(data);
    return v && typeof v === "object" ? (v as Record<string, unknown>) : undefined;
  } catch {
    return undefined;
  }
}

export function apply(t: Transcript, ev: SseEvent): Transcript {
  const d = json(ev.data);
  if (!d) return t;
  switch (ev.event) {
    case "meta":
      return typeof d.conversation_id === "string" ? { ...t, conversationId: d.conversation_id } : t;
    case "token":
      return typeof d.text === "string" ? { ...t, text: t.text + d.text } : t;
    case "done":
      return { ...t, done: true };
    default:
      return t;
  }
}
