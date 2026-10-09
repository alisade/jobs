# Rubric: fde/w4-t1 Managed Agents gateway: one customer sees another customer's cart
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: names the module-level `_current` dict in `gateway/identity.py` (PR #388) as shared mutable state across all in-flight requests on one event loop: middleware binds, then awaits the rate limiter (a suspension point), another request's bind overwrites the slot, and the first request's handler reads the wrong principal; also notes the second read after `sessions.load` and the no-op `release`. Partial (10-15): "a race in identity" without the mechanism (await between bind and read, one shared slot per process). Zero: blames the TTL, httpx, or the executor cache. |
| 3 | Evidence | 20 | Full: probe output and audit lines showing `customer=<X> session=gw-<Y>` with X != Y, plus a minimal repro or reasoning that ties it to concurrency (one account cannot reproduce; latency of the awaited Redis call widens the window). Partial: probe output only. Zero: assertion without evidence. |
| 4 | Red herring ruled out | 10 | Full: shows the session cache is keyed by principal (so a longer TTL cannot hand A's session to B) and/or that the race reproduces with TTL 0; dismisses the httpx pool warning with a reason. Partial: dismissed without evidence. Zero: changed the TTL as the fix. |
| 5 | Fix quality | 10 | Full: `ContextVar` (or request-scoped value passed explicitly) with `release` resetting the token in `finally`; API kept; no locks serializing all requests. Partial: works but serializes requests (global lock) or leaves the stale binding after the request. Zero: no fix. |
| 6 | Production follow-through | 5 | Guardrails: concurrency test in CI, lint/review rule against module-level request state, customer remediation (affected carts/sessions), ship the fix without reverting the rate limiter. |
Total: 100
