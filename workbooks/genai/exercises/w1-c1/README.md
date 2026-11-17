# genai/w1-c1 - Streamed shopping-assistant panel (React + TypeScript)

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 1 (React + TypeScript, streaming a
model response into the UI, testing with React Testing Library)

## Scenario

Kestrel Outfitters (a fictional outdoor and home-goods retailer, 140 stores plus the web shop) is adding
a shopping assistant to the product pages. The assistant gateway streams the model's answer as
Server-Sent Events. A prototype panel worked in the demo, where the dev server flushed one whole event
per chunk. In the staging environment, behind the CDN and the load balancer, it shows garbled JSON, drops
words, keeps "typing" forever when the connection drops, and has no way to stop a long answer.

You own the panel for the beta. The design review asked for: stop, retry, clear errors, product cards from
the structured events (not from the text), the AI disclosure, and a "talk to a person" handoff.

## Stream contract (assistant gateway)

`POST /api/assistant/stream` with JSON `{"prompt": "...", "conversation_id": "c-..." | null}` and
`Accept: text/event-stream`. The response is `text/event-stream`:

| event | data (JSON) | meaning |
|---|---|---|
| `meta` | `{"conversation_id", "model"}` | first event; send `conversation_id` with the next question |
| `token` | `{"text"}` | append to the answer; has an `id:` |
| `product` | `{"sku", "name", "price_cents", "in_stock", "url"}` | render a product card |
| `error` | `{"code", "message", "retryable"}` | the answer failed; show `message` |
| `done` | `{"stop_reason", "usage"}` | the answer is complete |

Comment lines (`: keepalive`) arrive every 10 s. Lines may end in LF or CRLF. Chunks arrive at arbitrary
boundaries: an event, a line, or a CRLF can be split across two chunks. `fixtures/` has two recorded streams.

## What you have

| Path | What it is |
|---|---|
| `src/sse.ts` | SSE parser (prototype: only works when each chunk is a whole event) |
| `src/events.ts` | typed events and `formatPrice` (complete, use it) |
| `src/openStream.ts` | fetch transport (prototype: buffers the whole body) |
| `src/useAssistantStream.ts` | the hook that runs one answer (prototype: happy path only) |
| `src/AssistantPanel.tsx` | the panel (prototype) |
| `tests/` | visible tests and helpers (`controlled()` lets a test push chunks one at a time) |

## Your task

1. `SseParser`: implement the event-stream rules listed in `src/sse.ts` so any chunking of a stream gives
   the same events.
2. `createOpenStream`: real streaming with `res.body.getReader()`, correct UTF-8 decoding across chunks,
   errors as `StreamHttpError`, and reader cancellation when the consumer stops early.
3. `useAssistantStream`: status `idle | streaming | done | stopped | error`, `stop()`, `retry()`, error
   events, thrown errors (use the exact `MESSAGES` strings: 429/503 -> `busy`, other HTTP errors ->
   `unavailable`, network failure or a stream that ends without `done` -> `connectionLost`), the
   conversation id, no stale updates after stop/new send/unmount, a repeated product SKU shown once.
4. `AssistantPanel`: the UI requirements below.
5. Fill in `ANSWER.md`.

Write the parser and the hook yourself before asking an assistant for help. In a live round you will be
asked to explain every line.

## UI requirements

- A disclosure that includes the words "AI assistant".
- `textarea` labelled "Ask about products"; "Send" is disabled while streaming or when the box is empty;
  the box clears after sending.
- While streaming: a "Stop" button and a `role="status"` line containing "typing". After stop: status
  "Stopped", partial answer kept, no error shown.
- The answer in a `role="log"` region named "Assistant answer" with `aria-live="polite"`.
- Product cards: `role="article"` named by the product name, with a link, the price (`$249.00`) and
  "In stock" / "Out of stock".
- Errors in a `role="alert"` with the message and, when retryable, a "Try again" button that re-sends the
  same prompt and clears the old partial answer.
- When `onHandoff` is given, a "Talk to a person" button that calls it with the conversation id.

## Acceptance criteria (what the grader checks)

- Any chunking of the recorded streams (one char at a time, every split point, CRLF split between chunks)
  gives identical events and identical rendered text.
- Stop aborts the request signal and ignores chunks that arrive afterwards; unmount aborts too.
- Error, drop, early end and HTTP failures show the right message; retry works.
- Transport decodes split multi-byte characters, rejects non-stream responses, cancels the reader early.
- Malformed or unknown events never crash the panel.

## How to run

```bash
make setup     # links the shared toolchain (first run installs it into genai/_env)
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade genai/w1-c1
make clean
```
