# ANSWER: connect/x-1 Duplicate ServiceNow incidents from the phone channel

## Approach

Took one duplicate pair from the ServiceNow export, followed its correlation_id (the ContactId) into the
flow logs, Lambda logs and traces, then compared timings across the day.

## Root cause

`grep -c correlation_id` style check: 135 pairs share a correlation_id, seconds apart. For one pair,
`grep <contact> incident/lambda-logs/*` shows ONE RequestId with `attempt=1 failed: network/timeout:
AbortError after 2501 ms; retrying in 200 ms` and `attempt=2 status=201`. traces/ shows the server
finished the first POST after the abort (e.g. 2,9xx ms), so ServiceNow committed it. The client
(`src/servicenow.ts`) retries every method on timeout/5xx, including a non-idempotent POST. Insert time
rose after the 2026-10-05 sync business rule change: p95 3,240 ms at 09-10 and 13 EDT vs 940 ms off-peak,
above the 2.5 s timeout, hence intermittent and worse in the morning. Connect double invocation ruled
out: one flow log line (Success) and one RequestId per contact.

## Fix

Contact id is the idempotency key: completed record short-circuit, lookup by correlation_id before
create, conditional claim (DynamoDB attribute_not_exists) so concurrent invocations wait, POST without
client retries, lookup after any ambiguous failure before retrying, 429 retried. Verified with the
commit-then-504 fake, concurrency and re-invoke tests.

## Trade-offs / what I would do in production

Daily duplicate-correlation report as an alarm; ask ServiceNow to make the rule async; keep the budget
inside Connect's 8 s; TTL 1 h on records; move to async create via SQS if latency keeps growing.
