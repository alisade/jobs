# Rubric: genai/w2-t1 Catalog search p95 went from 80 ms to 4 s
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh (two guards pass on the starter) |
| 2 | Root cause identified | 25 | Full: the `async def search` endpoint calls the synchronous PromoHub SDK, which blocks the event loop thread for the whole round trip; with one uvicorn worker per pod every other request on that pod, including `/healthz`, queues behind it, so latency stacks up (about 0.25 s x requests in flight) and liveness probes time out and restart pods. More pods do not help because each pod still serializes its own requests and the HPA reacts to in-flight requests, not CPU. Partial (10-15): "the SDK is slow" or "the new promotions call" without the event-loop blocking mechanism. Zero: the database, PromoHub outage, or traffic. |
| 3 | Evidence | 20 | Full: at least three of: py-spy MainThread inside `badges_for` in every sample while the AnyIO worker thread is idle; `/healthz` p95 going from 2 ms to seconds (a trivial handler cannot be slow on its own); CPU at 9 percent (waiting, not computing); PromoHub's own p50 0.24 s unchanged; the before/after table; `make demo` output. Partial: one or two. |
| 4 | Red herring ruled out | 5 | The slow query is 3.7 ms mean (logged only because the threshold is 2 ms) and unchanged; the index would not move a 4 s p95. Traffic at 1.5x cannot explain 50x. |
| 5 | Fix quality | 10 | The SDK call runs off the loop (`run_in_threadpool`, `anyio.to_thread`, or a plain `def` endpoint) with the SDK's timeout set, errors caught and degraded, no call on empty results; the SDK file untouched. Mentions the threadpool size (40 by default) as the new limit. |
| 6 | Prevention | 10 | Concrete: an async client or a badge cache refreshed in the background, event-loop lag metric and alert, a test or lint rule for blocking calls in `async def`, a concurrency test in CI like the hidden ones, separate liveness (process alive) from readiness. Partial: generic "load test more". |
Total: 100
