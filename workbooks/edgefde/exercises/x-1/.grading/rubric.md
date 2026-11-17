# Rubric: edgefde/x-1 CMMS work-order client: retries, Retry-After and idempotency keys
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 55 | points = 55 * passed / total from grade.sh |
| 2 | Idempotency reasoning | 15 | ANSWER.md: a lost response after commit is indistinguishable from a failed request, so retries without a key create duplicates; the key must come from the anomaly (machine + window), not a random UUID per call, so restarts and other gateways agree. |
| 3 | Retry design | 15 | Single loop, classified errors, full jitter with cap, Retry-After precedence, budget checked before sleeping, 401 refresh outside the attempt count. |
| 4 | Code quality | 5 | Typed, small, no bare except, clear errors. |
| 5 | Production notes | 10 | httpx with explicit timeouts and pooling, secrets from a vault, an outbox or queue when the CMMS is down for hours, metrics and logs per retry, circuit breaker. |
Total: 100
