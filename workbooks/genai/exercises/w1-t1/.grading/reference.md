# Reference: genai/w1-t1

## Root cause
`streamAnswer` replaces the parser at the end of a failed connection (`parser = new SseParser()`, added
in WEB-3391 so a half-received event cannot leak) and then, at the top of the loop, reads
`const lastEventId = parser.lastEventId` from the NEW parser. That is always undefined, so every
reconnect sends an empty `Last-Event-ID`. The gateway treats an empty id as "replay the buffered answer
from id 1" (gateway.log), and `transcript.apply` appends every token it receives. The words before the
drop are rendered twice.

## Evidence chain
- HAR entry 1: `last-event-id:` (empty), body starts at `id: 1` again.
- client-console.log: `connect #2 last-event-id=`.
- gateway.log: `client disconnected, sent_through_id: 8` then `resume: no last_event_id, replaying ...
  from id 1`.
- edge-proxy.log: `upstream_idle_timeout=15000ms ... reason="idle timeout"` 15 s after the stream started,
  while the gateway waited on `check_inventory`; 1,912 such closes since the migration and none before.
- Screenshot: the repeated text is exactly tokens 1-8.

## Trigger vs cause
The reconnect code shipped the same day as CHG-8812. Before the migration (120 s idle timeout) streams
almost never dropped, so the bug was latent. The proxy's 15 s idle timeout cuts long answers during a
tool call, which is when no bytes flow. StrictMode is a development-only behaviour; the duplicated bytes
are in the network trace, so rendering is not the source.

## Fix
- Keep `lastEventId` outside the loop and set it from each dispatched event (`ev.id`). Copying
  `parser.lastEventId` from the old parser is almost right but wrong for a half event: the parser records
  the `id:` line before the event is complete, so the client would resume after a token it never applied.
- Make `apply` idempotent: track the highest applied token id and ignore a token whose id is not
  greater. This protects against any replay (old gateway pod, expired buffer, a proxy retry).

## Prevention
- Keepalive comments from the gateway every 5-10 s; raise the idle timeout on the stream route; document
  the timeout chain (browser, edge, ALB, gateway) for streaming routes.
- A reconnect test with a fake gateway (like `tests/gateway.ts`) in CI.
- Metrics: reconnects per answer, resumes with an empty id (should be zero), replayed token count.
