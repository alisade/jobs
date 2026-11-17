# Rubric: connect/x-1 Duplicate ServiceNow incidents from the phone channel
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: a non-idempotent POST is retried after an ambiguous failure: at peak ServiceNow insert time (sync business rule changed 2026-10-05) exceeds the client's 2.5 s per-attempt timeout, the client aborts, ServiceNow still commits, the client retries and commits a second incident; only calls whose insert took > 2.5 s duplicate, which is why mornings (09-10, 13 EDT peaks). Partial (10-15): "retries cause duplicates" without the ambiguous-commit mechanism or without the timing link. Zero: blames Connect double invocation or ServiceNow alone. |
| 3 | Evidence | 20 | Full: quotes a duplicate pair (same correlation_id, seconds apart), the matching Lambda log (attempt 1 AbortError after 2501 ms, attempt 2 201) under ONE RequestId, the trace line showing the server finished after the abort, and the transaction-time p95 above 2.5 s at peak hours. Partial: one or two pieces. |
| 4 | Red herring handled | 5 | Rules out Connect re-invocation: one flow log line and one Lambda RequestId per contact, Results Success; notes that Connect can retry failed invocations in general, which the fix also covers. |
| 5 | Fix quality | 10 | Contact id as idempotency key (correlation_id + claimed record); lookup by correlation_id before create and after any ambiguous failure; no blind POST retry; 429 retried (safe, not processed); concurrent invocations wait for the winner; within the flow's 8 s budget; no deletion-based "dedupe". |
| 6 | Prevention / production | 10 | Concrete: alarm on duplicate correlation_id (scheduled ServiceNow report or a metric), timeout budget aligned with ServiceNow latency SLO and the Connect limit, TTL choice, ask ServiceNow to make the business rule async, unique index on correlation_id for the integration user if allowed, idempotency in the shared client for all writers. Partial: generic. |
Total: 100
