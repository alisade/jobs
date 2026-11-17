# ANSWER: awsfde/w1-t1 Throttling storm after the resilience release

## Approach

Compared the two Mondays in run/dashboard.txt, then counted calls per request in the logs, then read
the release diff with the botocore retry semantics in mind. Checked concurrency and quota last.

## Root cause

Two stacked retry layers. `Config(retries={"max_attempts": 10})` means 10 retries: the client reports
`{'mode': 'standard', 'total_max_attempts': 11}`. The new `call_with_retries` wraps that in 5 app
attempts with a fixed 1 s delay, no jitter, and retries every ClientError. One request can make
5 x 11 = 55 calls; the logs show up to 21 before the 60 s Lambda timeout:

    {"request_id": "20261109-03052", "status": 504, "lambda_duration_ms": 60000, "model_calls": 21, ...}

ValidationException requests now make 5 calls each (previous release: 1).

Dashboard: 2026-11-02 bedrock_inv 6,684, throttles 532, max_conc 41. 2026-11-09 bedrock_inv 20,863,
throttles 12,382, max_conc 150, p95 29,000 ms from 09:02 to 09:10. The 09:02 login wave starts it;
retried calls keep the bucket empty so new requests get throttled and join the pool; the gateway
returns 504 at 29 s while the Lambda keeps calling; the portal retries once on 504/500/429. It drains
only at ~09:12.

## Fix

SDK layer only: `{"total_max_attempts": 3, "mode": "standard"}` (jittered backoff). App policy makes
one attempt and only ever retries transient codes with capped full jitter. Exhausted throttling
returns 503 with Retry-After 30; ValidationException 400; anything else 500. `make replay`:
error_rate 0.021, p95 3,521 ms, 7,841 calls for 7,381 requests.

Not causes: reserved concurrency (peak 41 last week, pinned at 150 only as a result of the retries;
the fix passes at 100) and the quota (unchanged).

## Trade-offs / what I would do in production

Alarm on InvocationThrottles/Invocations and calls per request; load-test the 09:00 wave; review rule
for retry layers; then size quota or use a cross-Region inference profile for real growth.
