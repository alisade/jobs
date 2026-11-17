// Test helpers: a stream the test controls chunk by chunk, and fixture loading.
import * as fs from "fs";
import * as path from "path";
import type { OpenStream, StreamRequest } from "../src/useAssistantStream";

export function fixture(name: string): string {
  return fs.readFileSync(path.join(__dirname, "..", "fixtures", name), "utf8");
}

/** Split a recorded stream at its event boundaries (what the dev server does). */
export function eventChunks(text: string): string[] {
  return text.split(/(?<=\n\n)/);
}

export interface Controlled {
  open: jest.Mock<AsyncIterable<string>, [StreamRequest, AbortSignal]> & OpenStream;
  push: (s: string) => void;
  end: () => void;
  fail: (e: unknown) => void;
  requests: StreamRequest[];
  signals: AbortSignal[];
}

/** An OpenStream whose chunks the test pushes one at a time; honours the AbortSignal. */
export function controlled(): Controlled {
  let q: string[] = [];
  let ended = false;
  let err: unknown = null;
  let wake: (() => void) | null = null;
  const requests: StreamRequest[] = [];
  const signals: AbortSignal[] = [];
  const open = jest.fn((req: StreamRequest, signal: AbortSignal) => {
    requests.push(req);
    signals.push(signal);
    q = [];
    ended = false;
    err = null;
    return {
      [Symbol.asyncIterator]() {
        return {
          async next(): Promise<IteratorResult<string>> {
            for (;;) {
              if (signal.aborted) {
                const e = new Error("The operation was aborted");
                e.name = "AbortError";
                throw e;
              }
              if (err) throw err;
              if (q.length) return { done: false, value: q.shift() as string };
              if (ended) return { done: true, value: undefined };
              await new Promise<void>((r) => {
                wake = r;
                signal.addEventListener("abort", () => r(), { once: true });
              });
            }
          },
          async return(): Promise<IteratorResult<string>> {
            ended = true;
            return { done: true, value: undefined };
          },
        };
      },
    };
  }) as unknown as Controlled["open"];
  const poke = () => {
    const w = wake;
    wake = null;
    if (w) w();
  };
  return {
    open,
    push: (s) => { q.push(s); poke(); },
    end: () => { ended = true; poke(); },
    fail: (e) => { err = e; poke(); },
    requests,
    signals,
  };
}

/** A whole recorded stream delivered in the given chunks, as an OpenStream. */
export function replay(chunks: string[]): jest.Mock & OpenStream {
  return jest.fn((_req: StreamRequest, signal: AbortSignal) => ({
    async *[Symbol.asyncIterator]() {
      for (const c of chunks) {
        if (signal.aborted) return;
        await Promise.resolve();
        yield c;
      }
    },
  })) as unknown as jest.Mock & OpenStream;
}
