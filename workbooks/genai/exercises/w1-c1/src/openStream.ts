// Production transport: POST to the gateway and yield decoded text chunks.
import type { OpenStream, StreamRequest } from "./useAssistantStream";

export class StreamHttpError extends Error {
  constructor(public status: number, message?: string) {
    super(message || `assistant stream failed with HTTP ${status}`);
    this.name = "StreamHttpError";
  }
}

type FetchLike = (url: string, init: RequestInit) => Promise<Response>;

// TODO:
//   - POST JSON {prompt, conversation_id} with Accept: text/event-stream and the AbortSignal
//   - non-2xx -> throw StreamHttpError(status)
//   - a 2xx that is not text/event-stream (a proxy error page, a buffered JSON body) is not a
//     stream -> throw StreamHttpError(502, ...)
//   - read res.body with a reader and decode UTF-8 correctly when a multi-byte character is
//     split across two chunks
//   - if the consumer stops early (break / return), cancel the reader so the connection closes
export function createOpenStream(fetchImpl: FetchLike, url = "/api/assistant/stream"): OpenStream {
  return async function* open(req: StreamRequest, signal: AbortSignal): AsyncGenerator<string> {
    const res = await fetchImpl(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: req.prompt }),
      signal,
    });
    const body = await res.text();
    yield body;
  };
}
