# Rubric: genai/w1-t1 Duplicated words in streamed answers after the proxy change
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh (several guards pass on the starter) |
| 2 | Root cause identified | 25 | Full: on reconnect `streamAnswer` reads `lastEventId` from the parser it just replaced (`parser = new SseParser()` happens before the next loop iteration reads `parser.lastEventId`), so every reconnect sends an empty Last-Event-ID; the gateway treats empty as "replay from id 1" and the reducer appends tokens blindly, so the first part of the answer appears twice. Partial (10-15): "the reconnect replays" without why the id is empty, or without the reducer appending. Zero: StrictMode, the model, or the proxy alone. |
| 3 | Evidence | 20 | Full: at least three quoted pieces: HAR entry 1 `last-event-id:` empty and replay starting at id 1; console `connect #2 last-event-id=`; gateway `resume: no last_event_id, replaying ... from id 1` and `sent_through_id: 8`; proxy `reason="idle timeout"` at 15 s during the `check_inventory` tool call; screenshot repeats exactly tokens 1-8. Partial: one or two pieces. |
| 4 | Trigger vs cause, red herring | 5 | The proxy idle timeout (CHG-8812, 15 s vs 120 s) is the trigger that made the latent reconnect bug visible on long answers with tool calls; StrictMode is dev-only and the duplicate bytes are on the wire in the HAR, not produced by rendering. |
| 5 | Fix quality | 10 | `lastEventId` carried across connections and taken from the last dispatched event (taking `parser.lastEventId` from the old parser is close but resumes after the `id:` line of a half-received event and skips that token), fresh parser kept, and the reducer ignores tokens with an already-applied id. Re-using one parser across connections (which would glue a half event to the next stream) loses points. |
| 6 | Prevention | 10 | Concrete: gateway or proxy keepalive comments every 5-10 s (shorter than any idle timeout on the path), raise the stream route's idle timeout, a reconnect test with a fake gateway in CI, a metric on reconnects and on resumes with an empty id, gateway rejecting an empty Last-Event-ID for a known conversation. Partial: generic "more tests". |
Total: 100
