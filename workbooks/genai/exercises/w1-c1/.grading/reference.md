# Reference: genai/w1-c1

The reference files are in `.grading/solution/src/`. Key points an interviewer looks for:

## Parser (`sse.ts`)
- Keep a line buffer across `push()` calls; split on the first `\r\n`, `\r` or `\n`; dispatch only on an
  empty line. A `\r` that ends a chunk is ambiguous (it may be half of `\r\n`), so remember it and drop a
  leading `\n` in the next chunk.
- `data:` lines accumulate and join with `\n`; strip exactly one leading space; `event:` resets after
  dispatch; `id:` persists (it is the value a reconnect sends as `Last-Event-ID`).
- Lines starting with `:` are comments (keepalives). An event with no data is not dispatched. At end of
  stream an unterminated event is discarded.

## Transport (`openStream.ts`)
- `fetch` instead of `EventSource`: the gateway needs POST with a JSON body and an `AbortSignal`;
  `EventSource` is GET-only and cannot send headers.
- `TextDecoder.decode(value, { stream: true })` so a multi-byte character split across chunks is not
  replaced with U+FFFD; call `decode()` once more at the end.
- Validate the content type: a CDN or proxy error page often arrives as `200 text/html`.
- Cancel the reader in `finally` when the consumer exits early, otherwise the connection (and the model
  generation behind it) keeps running.

## Hook (`useAssistantStream.ts`)
- One `AbortController` per run plus a run counter; every state write checks the run is still current.
  This is what makes Stop, a quick second Send and unmount safe.
- Functional updates (`setText(t => t + ev.text)`), because tokens arrive faster than renders.
- A stream that ends without `done` is an error ("connection lost"), not a success: otherwise a dropped
  connection looks like a complete, truncated answer.
- `AbortError` after Stop is expected and is not shown.

## Panel
- Products come from structured `product` events, never parsed out of the text.
- `role="log"` with `aria-live="polite"` for the answer, `role="alert"` only for errors, the AI disclosure,
  and a handoff path (People + AI Guidebook, Microsoft HAX guidelines).

## Production notes
- Reconnect: either resume with `Last-Event-ID` (server must buffer by id) or re-ask; never append a
  replay to the existing text (see w1-t1).
- Proxies: disable response buffering for the stream route, send keepalive comments more often than the
  shortest idle timeout on the path.
- Rendering: at high token rates batch updates per animation frame.
- Measure time to first token, completion rate, stop rate, error rate by code.
