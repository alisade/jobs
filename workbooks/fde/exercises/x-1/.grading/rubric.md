# Rubric: fde/x-1 Halyard risk-API client: token cache, latency budget, circuit breaker
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 45 | points = 45 * passed / total from grade.sh |
| 2 | Concurrency correctness | 15 | Full: token fetch under an `asyncio.Lock` with a re-check after acquiring (double-checked), invalidation only of the token the caller used, half-open trial slot taken atomically (no await between check and set), released in `finally` on cancellation. Partial: lock present but re-check missing or invalidation races. Zero: no single flight. |
| 3 | Budget and cancellation semantics | 15 | Full: one `asyncio.timeout` around token + assess + retry; `TimeoutError` caught outside it and re-raised as `RiskTimeout ... from None`; no `except BaseException`/bare except swallowing `CancelledError`; no retry loop that can exceed the budget. ANSWER.md explains where cancellation can arrive. Partial: budget per-request instead of per-call. Zero: `wait_for` per hop or retries with sleeps. |
| 4 | Error taxonomy | 10 | Full: no httpx exception leaks; 4xx vs 5xx/429 distinction preserved; breaker counts only unavailability; messages carry status/class names, not secrets or bodies. Partial: one leak path. Zero: raw httpx errors escape. |
| 5 | Code quality and testability | 5 | Injected clock used consistently (token expiry and breaker), typed, small functions, no globals. |
| 6 | ANSWER.md trade-offs | 10 | Full: takes positions on at least two of: per-process breaker state with N workers, consecutive vs rate-based tripping, background token refresh, retry budgets, the metrics/alerts to emit. Partial: generic. Zero: empty. |
Total: 100
