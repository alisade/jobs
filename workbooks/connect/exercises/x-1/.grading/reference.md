# Reference: connect/x-1

Root cause: `ServiceNowClient.request` retries every method on timeouts and 5xx. On 2026-10-05 a
ServiceNow business rule ("LFG - Assignment group lookup (sync)") made incident inserts slower; at the
09:00-10:00 and 13:00 EDT peaks p95 insert time is ~3.2 s, above the client's 2.5 s per-attempt
timeout. The client aborts, ServiceNow still commits (first incident), the client retries the POST
(second incident) and returns the second number to Connect. Calls under 2.5 s never duplicate, so
the problem is intermittent and worse at peaks.

Evidence: a pair in `servicenow/incident-export-*.csv` with the same correlation_id; the same
contact in `lambda-logs/` under a single RequestId with `attempt=1 failed: network/timeout:
AbortError after 2501 ms` then `attempt=2 status=201`; `traces/` showing the server finished after
the abort; `transaction-times` p95 3,240 ms at peaks.

Red herring: Connect does retry failed Lambda invocations in general, but here each contact has one
flow log line (Results Success) and one RequestId, so the duplicates are inside one invocation.

Fix (`.grading/solution/src/handler.ts`): contact id as the idempotency key; completed record ->
return it; lookup by `correlation_id` before creating; conditional claim so concurrent invocations
wait for the winner; POST without client retries; on an ambiguous failure look up by correlation_id
before trying again; retry 429 (safe: not processed). Covers Connect re-invocations too.

Production: alarm on duplicate correlation_id (scheduled report), make the business rule async or
raise the budget consciously (Connect sync limit 8 s, chain cap 20 s), consider an async create
(return immediately, create in a queue consumer with the same key) if ServiceNow latency keeps
growing; never "dedupe" by deleting records (audit trail).
