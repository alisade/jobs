// Reconnecting SSE client used by the storefront assistant panel (release 2026.11.04).
//
// The gateway gives every token event an id. When a connection drops before "done", the client
// reconnects (up to maxReconnects times) and sends the last id it saw as Last-Event-ID; the gateway
// then resumes after that id instead of starting the answer again.
import { SseParser, type SseEvent } from "./sse";
import { apply, empty, type Transcript } from "./transcript";

export interface ConnectRequest {
  prompt: string;
  conversationId?: string;
  /** Sent as the Last-Event-ID header. Undefined or "" means "start from the beginning". */
  lastEventId?: string;
}

/** One HTTP connection to the gateway; yields raw text chunks until the connection ends or fails. */
export type Connect = (req: ConnectRequest, signal: AbortSignal) => AsyncIterable<string>;

export interface StreamOptions {
  maxReconnects?: number;
  signal?: AbortSignal;
  onUpdate?: (t: Transcript) => void;
  log?: (line: string) => void;
}

export type Outcome = "done" | "failed" | "aborted";

export interface StreamResult {
  outcome: Outcome;
  transcript: Transcript;
  connections: number;
}

function isAbort(e: unknown): boolean {
  return !!e && typeof e === "object" && (e as { name?: string }).name === "AbortError";
}

export async function streamAnswer(
  connect: Connect,
  prompt: string,
  opts: StreamOptions = {},
): Promise<StreamResult> {
  const maxReconnects = opts.maxReconnects ?? 3;
  const signal = opts.signal ?? new AbortController().signal;
  const log = opts.log ?? (() => undefined);
  let transcript = empty;
  let connections = 0;
  let parser = new SseParser();

  for (;;) {
    const lastEventId = parser.lastEventId;
    connections++;
    log(`[assistant] connect #${connections} last-event-id=${lastEventId ?? ""}`);
    try {
      for await (const chunk of connect({ prompt, conversationId: transcript.conversationId, lastEventId }, signal)) {
        for (const ev of parser.push(chunk)) {
          transcript = apply(transcript, ev as SseEvent);
          opts.onUpdate?.(transcript);
          if (transcript.done) return { outcome: "done", transcript, connections };
        }
      }
      log(`[assistant] connection #${connections} ended before done`);
    } catch (e) {
      if (isAbort(e) || signal.aborted) return { outcome: "aborted", transcript, connections };
      log(`[assistant] connection #${connections} failed: ${String(e)}`);
    }
    if (signal.aborted) return { outcome: "aborted", transcript, connections };
    if (connections > maxReconnects) return { outcome: "failed", transcript, connections };
    // Start the next connection with a fresh parser, so a half-received event from the dead
    // connection cannot leak into the new one.
    parser = new SseParser();
  }
}
