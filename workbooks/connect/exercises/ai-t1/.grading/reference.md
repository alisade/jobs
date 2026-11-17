# Reference: connect/ai-t1

Mechanism: the flow block waits at most 8 s (synchronous mode). The function's own timeout was 30 s,
so when Bedrock was slow the Lambda kept running and later returned "OK" to nobody: Lambda Errors = 0,
flow logs show Results "Error" for the same contacts. Inside those invocations the trace samples show
HTTP 429 ThrottlingException, SDK backoff (standard retry mode, 3 attempts by default), another 429,
more backoff, then a 2.5-4 s generation of 500-1000 output tokens (maxTokens 2048 never bound it).
Throttling started at 14:00 because the analytics backfill (14:02-15:30) used the same model's
on-demand quota in the same account (Bedrock InvocationThrottles 0 -> 412 -> 198).

Memory: Max Memory Used is ~230-250 MB on fast and slow runs alike; the time is spent waiting.

Fix (`.grading/solution/`): deadline = min(FLOW_BUDGET_MS 6500, remaining time) - 300 ms; race the
Converse call against the deadline and abort it; DEGRADED with reason timeout/throttled/error instead of
throwing; maxAttempts 2; maxTokens 350 (capped at 400); empty transcript short-circuits; function Timeout 8.

Follow-ups: separate real-time and batch capacity (different account/quota, cross-region inference
profile for the batch job, or throttle the backfill), async Lambda mode (up to 60 s; Wait + Load Lambda
result) or move the summary after the transfer, a "one moment" prompt to cover latency, alarms on
Duration p99 > 6 s and on the degraded rate.
