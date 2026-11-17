// A fake assistant gateway for tests: serves a recorded answer, can drop connections, and
// resumes after Last-Event-ID like the real gateway (or ignores it, like an old gateway build).
import type { Connect, ConnectRequest } from "../src/streamClient";

export interface Ev { id?: string; event: string; data: string }

export const WORDS = ["For ", "two ", "people ", "on ", "a ", "weekend ", "trip, ", "the ", "Ridgeline ", "2P ", "is ", "the ", "best ", "fit."];
export const FULL = WORDS.join("");

export function answer(words: string[] = WORDS): Ev[] {
  const evs: Ev[] = [{ event: "meta", data: JSON.stringify({ conversation_id: "c-7f3a91", model: "primary" }) }];
  words.forEach((w, i) => evs.push({ id: String(i + 1), event: "token", data: JSON.stringify({ text: w }) }));
  evs.push({ event: "done", data: JSON.stringify({ stop_reason: "end_turn" }) });
  return evs;
}

export function frame(e: Ev): string {
  return (e.id !== undefined ? `id: ${e.id}\n` : "") + `event: ${e.event}\ndata: ${e.data}\n\n`;
}

export interface Plan {
  /** per connection: how many events to send before the connection drops (undefined = no drop) */
  dropAfter?: (number | undefined)[];
  /** drop by throwing (TypeError) instead of a clean close */
  throwOnDrop?: boolean;
  /** send half of the next event before dropping */
  partialOnDrop?: boolean;
  /** old gateway build: always replays from the start */
  ignoreLastEventId?: boolean;
}

export function gateway(events: Ev[], plan: Plan = {}) {
  const requests: ConnectRequest[] = [];
  const connect: Connect = (req, signal) => {
    const n = requests.length;
    requests.push({ ...req });
    let start = 0;
    if (!plan.ignoreLastEventId && req.lastEventId) {
      const idx = events.findIndex((e) => e.id === req.lastEventId);
      start = idx >= 0 ? idx + 1 : 0;
    }
    const limit = plan.dropAfter ? plan.dropAfter[n] : undefined;
    return {
      async *[Symbol.asyncIterator]() {
        let sent = 0;
        for (let i = start; i < events.length; i++) {
          if (signal.aborted) return;
          if (limit !== undefined && sent >= limit) {
            if (plan.partialOnDrop) yield frame(events[i]).slice(0, 12);
            if (plan.throwOnDrop) throw new TypeError("network error");
            return;
          }
          await Promise.resolve();
          yield frame(events[i]);
          sent++;
        }
      },
    };
  };
  return { connect, requests };
}
