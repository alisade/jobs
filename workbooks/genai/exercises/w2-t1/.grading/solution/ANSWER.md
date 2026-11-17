# ANSWER: genai/w2-t1 Catalog search p95 went from 80 ms to 4 s

## Approach

I started from the strangest symptom: `/healthz` slow. It returns a constant, so it can only be slow if it
cannot get scheduled. Next I read the py-spy dump and the release notes, then reproduced the problem
with `make demo`. The probes showed 2-4.6 s, and search p95 was 4.8 s with PromoHub at 0.25 s.

## Root cause

`search` is `async def` and calls the synchronous PromoHub SDK (`badges_for`) directly. That blocks the
only event loop on the pod for each 0.25 s round trip. Every other request on that pod, `/healthz`
included, waits behind it.
- py-spy: `Thread 1 "MainThread"` in `sleep` <- `badges_for (promotions_sdk.py:46)` <- `search (app.py:37)`,
  in all 4 samples; `AnyIO worker thread` idle.
- `/healthz` p95 went from 0.002 s (before the release) to 3.90 s at 09:10. Kubelet events:
  `Liveness probe failed ... context deadline exceeded`, then `Killing`.
- CPU is 0.09 of 1.0 cores, so the thread is waiting, not working. PromoHub's own p95 is 0.31 s, so the
  vendor is fine.
- Scale-out to 12 pods did not help, because every pod still serializes its own requests behind the
  blocking call. The restarts also drop in-flight requests.

The slow query is not the cause. It runs in 3.7 ms on average (max 9.8 ms) and is logged only because
the threshold is 2 ms. Traffic is up 1.5x and latency is up 50x.

## Fix

The SDK call now runs in the threadpool with the SDK's own timeout (`PROMO_TIMEOUT_S=0.3`).
`PromotionsError` (timeouts included) returns results without badges and `promotions_degraded: true`,
and an empty result skips the call. After the fix `make demo` shows probes in milliseconds and search
p95 near 0.3 s. All tests pass.

## Trade-offs / what I would do in production

- The threadpool (40 threads by default) is now the cap on concurrent PromoHub calls. Next step: an async
  client, or a badge cache refreshed in the background.
- I would add an event-loop lag metric with an alert, a CI test that checks health latency under slow
  requests, and a lint rule for blocking calls in `async def`.
- I would make liveness independent of request load.
