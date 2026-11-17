# ANSWER: genai/w1-t1 Duplicated words in streamed answers after the proxy change

## Approach

I started with the screenshot and the HAR export. One question produced two POSTs to the stream
endpoint, and the second body started again at `id: 1`, so the duplicate text was on the wire, not made
by React. I then lined up the console, edge proxy and gateway logs by time and read `streamClient.ts`
against them. I reproduced it with the fake gateway (`dropAfter: [6]`).

## Root cause

On reconnect the client sends an empty `Last-Event-ID`. `streamAnswer` replaces the parser after a failed
connection (`parser = new SseParser()`), then reads `const lastEventId = parser.lastEventId` from the new
parser at the top of the loop. That value is always undefined. The gateway treats an empty id as "replay
from the start", and `transcript.apply` appends every token, so tokens 1-8 render twice.

Evidence:
- `network-trace.txt`, entry 1: `last-event-id:` is empty and the body starts with `id: 1 ... "For "`.
- `client-console.log`: `connect #2 last-event-id=` right after `connection #1 ended before done`.
- `gateway.log`: `"client disconnected","sent_through_id":8` and then `"resume: no last_event_id,
  replaying buffered answer from id 1"`.
- `user-screenshot.txt`: the repeated text, "For two people on a weekend trip, the", is exactly tokens
  1-8.

The proxy is the trigger, not the cause. `edge-proxy.log` shows `upstream_idle_timeout=15000ms ...
reason="idle timeout"` 15 s into the stream, while the gateway waited on `check_inventory` and sent no
bytes. There are 1,912 such closes since CHG-8812 and none before it, because the old idle timeout was
120 s. The reconnect code (WEB-3391) shipped the same day, so the bug only shows on long answers with a
tool call. StrictMode is dev-only, and the duplicate bytes are already in the HAR, so it is not involved.

## Fix

- `streamClient.ts`: `lastEventId` now lives outside the loop and is set from each dispatched event. I did
  not copy `parser.lastEventId`, because it also picks up the `id:` line of a half-received event and the
  resume would skip that token. I kept the fresh parser per connection so a half event is dropped.
- `transcript.ts`: tokens are applied idempotently. The reducer tracks `lastSeq` and ignores any token
  whose id is not greater than it.
- Verified: `make test` passes, including the repro. I also checked two drops, a half event before the
  drop, and a gateway that ignores Last-Event-ID.

## Trade-offs / what I would do in production

- The gateway should send keepalive comments every 5-10 s, below every idle timeout on the path. Ask the
  edge team to raise the idle timeout on the stream route.
- The gateway should log a warning on an empty Last-Event-ID for a conversation it is still buffering.
- Add a CI test with a fake gateway that drops connections.
- Add metrics for reconnects per answer and resumes with an empty id.
- Idempotent apply costs one integer of state and protects against any replay source.
