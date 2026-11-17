# Rubric: javaai/w4-t1 The tutor is slow at 09:00 and some answers never arrive
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: the `async def` handler calls the synchronous Gemini SDK, blocking the single event loop, so each instance serves one turn at a time (log: turns finish back to back every ~2.3 s per instance) while up to 80 requests queue on it; Cloud Run scales on in-flight requests vs containerConcurrency (80) and CPU, and neither threshold is reached (71 in flight, CPU 9%: the thread is waiting, not computing), so it does not add instances; queueing plus a 30 s timeout gives the 504s; probes time out on the same blocked loop. Partial (10-15): "blocking call" without the autoscaling mechanism, or concurrency too high without the event loop. Zero: cold starts, Gemini latency. |
| 3 | Evidence | 20 | Quotes instance counts vs maxScale, max concurrent per instance vs CPU, the serial modelMs log lines, unchanged Vertex latency and no 429s, the probe timeout, and `make load` wall time before and after. |
| 4 | Red herring handled | 10 | Cold starts happened (one new instance, 3.7 s first request) but explain a few seconds on a few requests, not 25 s p95 on warm instances; min instances 5 costs always-on CPU and would still serve one turn at a time each. |
| 5 | Fix quality | 10 | `def` handler (threadpool) or an async client / `asyncio.to_thread`; containerConcurrency sized to the thread pool and the per-turn memory; timeout >= 120 (or streaming); ingress unchanged. |
| 6 | Production follow-ups | 5 | Load test of the ramp in CI or before cohorts, streaming SSE for long answers (time to first token), CPU always-allocated if streaming after response, alert on in-flight per instance vs CPU divergence. |
Total: 100
