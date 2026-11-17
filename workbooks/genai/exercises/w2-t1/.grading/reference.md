# Reference: genai/w2-t1

## Root cause
`search` is declared `async def`, so FastAPI runs it on the event loop thread. Inside it calls the vendor
SDK's synchronous `badges_for`, which blocks that thread for the full PromoHub round trip (about
0.25 s). Each pod runs one uvicorn worker, so one event loop handles every request on the pod. While a
search waits on PromoHub nothing else on the pod runs, not even `/healthz`. With N requests in flight
the last one waits about N x 0.25 s. That is why p95 is 4 s while PromoHub's own p50 is still 0.24 s.
The kubelet's 1 s probe timeout then fails three times and the pod restarts, which drops its in-flight
requests and makes the others worse. The HPA added pods, but each new pod serializes its own requests
in the same way, so the per-pod queue only gets shorter in proportion. CPU stays at 9 percent because
the thread is waiting, not computing.

Evidence: the py-spy dump shows MainThread inside `badges_for` in all 4 samples, with the AnyIO worker
thread idle. `/healthz` p95 goes from 2 ms to 3.9 s, and a handler that returns a constant cannot be slow
by itself. `make demo` shows probes taking seconds.

Red herring: the query takes 3.7 ms mean. It is logged only because `log_min_duration_statement` is
2 ms, and it is unchanged from before. The 1.5x traffic increase is real but cannot produce a 50x jump.

## Fix (solution/catalog_search/app.py)
`await run_in_threadpool(promotions.badges_for, skus, PROMO_TIMEOUT_S)`, catch `PromotionsError`
(timeouts included), set `promotions_degraded`, and skip the call for empty results. Alternatives that
also pass: a plain `def` endpoint (FastAPI runs it in the threadpool), or `anyio.to_thread.run_sync`.
The threadpool is now the concurrency limit (40 tokens by default), so the timeout matters.

## Prevention
- Prefer an async HTTP client for PromoHub, or a badge cache that a background task refreshes, so search
  never waits on the promotions engine.
- Alert on event-loop lag. Add a CI concurrency test: health check latency while slow requests run.
- Ban blocking calls in `async def`: code review rule, lint (for example flake8-async), or test with
  asyncio debug mode and `slow_callback_duration`.
- Keep liveness cheap and separate from readiness. A blocked loop should mark the pod not ready
  instead of getting it restarted in a loop.
