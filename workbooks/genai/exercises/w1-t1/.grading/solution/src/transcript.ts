// Turns assistant gateway events into the answer the panel renders.
import type { SseEvent } from "./sse";

export interface Transcript {
  text: string;
  done: boolean;
  conversationId?: string;
  /** Highest token id applied; a replayed token (same or lower id) is ignored. */
  lastSeq?: number;
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
      if (typeof d.text !== "string") return t;
      if (ev.id !== undefined && /^\d+$/.test(ev.id)) {
        const seq = Number(ev.id);
        if (t.lastSeq !== undefined && seq <= t.lastSeq) return t; // replay: already applied
        return { ...t, text: t.text + d.text, lastSeq: seq };
      }
      return { ...t, text: t.text + d.text };
    case "done":
      return { ...t, done: true };
    default:
      return t;
  }
}
