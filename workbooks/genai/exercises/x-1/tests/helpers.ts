// Test helpers: flag client, legacy search, analytics sink and a controllable assistant stream.
import type { FlagClient, FlagValues, AnalyticsEvent } from "../src/rollout";
import type { LegacyResult } from "../src/LegacySearch";
import type { OpenStream, StreamRequest } from "../src/vendor/useAssistantStream";

export function fakeFlags(initial: FlagValues) {
  let v = initial;
  const subs = new Set<(v: FlagValues) => void>();
  const client: FlagClient = {
    get: () => v,
    subscribe: (fn) => {
      subs.add(fn);
      return () => subs.delete(fn);
    },
  };
  return { client, set: (next: Partial<FlagValues>) => { v = { ...v, ...next }; subs.forEach((f) => f(v)); }, subscribers: () => subs.size };
}

export const RESULTS: LegacyResult[] = [
  { sku: "KO-TENT-2P", name: "Ridgeline 2P Tent", price_cents: 24900 },
  { sku: "KO-TENT-3P", name: "Basecamp 3P Tent", price_cents: 32900 },
];

export function fakeSearch(results: LegacyResult[] = RESULTS) {
  return jest.fn(async (_q: string) => results);
}

export function sink() {
  const events: AnalyticsEvent[] = [];
  return { track: jest.fn((e: AnalyticsEvent) => { events.push(e); }), events };
}

export const tok = (id: number, text: string) => `id: ${id}\nevent: token\ndata: ${JSON.stringify({ text })}\n\n`;
export const META = 'event: meta\ndata: {"conversation_id": "c-5501", "model": "primary"}\n\n';
export const DONE = 'event: done\ndata: {"stop_reason": "end_turn"}\n\n';

/** An OpenStream whose chunks the test pushes; honours the AbortSignal. */
export function controlled() {
  let q: string[] = [];
  let ended = false;
  let wake: (() => void) | null = null;
  const requests: StreamRequest[] = [];
  const signals: AbortSignal[] = [];
  const open = jest.fn((req: StreamRequest, signal: AbortSignal) => {
    requests.push(req);
    signals.push(signal);
    q = [];
    ended = false;
    return {
      [Symbol.asyncIterator]() {
        return {
          async next(): Promise<IteratorResult<string>> {
            for (;;) {
              if (signal.aborted) {
                const e = new Error("aborted");
                e.name = "AbortError";
                throw e;
              }
              if (q.length) return { done: false, value: q.shift() as string };
              if (ended) return { done: true, value: undefined };
              await new Promise<void>((r) => {
                wake = r;
                signal.addEventListener("abort", () => r(), { once: true });
              });
            }
          },
          async return(): Promise<IteratorResult<string>> {
            return { done: true, value: undefined };
          },
        };
      },
    };
  }) as unknown as jest.Mock & OpenStream;
  const poke = () => { const w = wake; wake = null; if (w) w(); };
  return { open, push: (s: string) => { q.push(s); poke(); }, end: () => { ended = true; poke(); }, requests, signals };
}

/** Find a user id that falls inside (or outside) a rollout percentage, using the code under test. */
export function userFor(modeForFn: (id: string, f: FlagValues) => string, inside: boolean, percent = 50): string {
  for (let i = 0; i < 10000; i++) {
    const id = `cust-${i}`;
    const m = modeForFn(id, { killSwitch: false, mode: "on", percent });
    if ((m === "on") === inside) return id;
  }
  throw new Error("no user id found");
}
