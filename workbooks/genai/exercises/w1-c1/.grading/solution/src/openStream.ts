// Production transport: POST to the gateway and yield decoded text chunks. Reference solution.
import type { OpenStream, StreamRequest } from "./useAssistantStream";

export class StreamHttpError extends Error {
  constructor(public status: number, message?: string) {
    super(message || `assistant stream failed with HTTP ${status}`);
    this.name = "StreamHttpError";
  }
}

type FetchLike = (url: string, init: RequestInit) => Promise<Response>;

export function createOpenStream(fetchImpl: FetchLike, url = "/api/assistant/stream"): OpenStream {
  return async function* open(req: StreamRequest, signal: AbortSignal): AsyncGenerator<string> {
    const res = await fetchImpl(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify({ prompt: req.prompt, conversation_id: req.conversationId ?? null }),
      signal,
    });
    const type = res.headers.get("content-type") || "";
    if (!res.ok) throw new StreamHttpError(res.status);
    if (!type.toLowerCase().startsWith("text/event-stream") || !res.body) {
      // a proxy error page or a buffered JSON body is not a stream
      throw new StreamHttpError(502, `expected text/event-stream, got "${type}"`);
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let complete = false;
    try {
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        const s = decoder.decode(value, { stream: true });
        if (s) yield s;
      }
      const tail = decoder.decode();
      if (tail) yield tail;
      complete = true;
    } finally {
      if (!complete) await reader.cancel().catch(() => undefined);
    }
  };
}
