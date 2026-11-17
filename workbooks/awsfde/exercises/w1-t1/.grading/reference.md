# Reference: awsfde/w1-t1

## Root cause

Release 2026.11.06 stacked two retry layers on every Bedrock call:

1. **SDK layer.** `Config(retries={"max_attempts": 10, "mode": "standard"})`. In botocore,
   `max_attempts` counts **retries**, not attempts: the client converts it to `total_max_attempts: 11`
   (check `client.meta.config.retries`). Standard mode backs off with jitter,
   `rand(0,1) * min(2 ** n, 20)` seconds.
2. **App layer.** `call_with_retries` with `RetryPolicy(max_attempts=5, delay 1 s, no jitter,
   retryable_codes=None)`: every `ClientError` is retried, including `ValidationException`
   (the ~1.5% oversized questions now make 5 calls each instead of 1) and the SDK's own exhausted
   throttling error.

So one user request can make up to 5 x 11 = 55 Bedrock calls; in the logs the 60 s Lambda timeout
cuts it at ~20 (`"model_calls": 21`, attempts listing app attempt 1 sdk attempts 1-11, then app
attempt 2 ...). The previous release made at most 3.

Why it became a storm: the 09:02 login wave (2x for 40 s, the same every Monday) briefly exceeds the
on-demand quota. Last week the excess requests failed fast (500, 3 attempts) and the system recovered
within the minute. This week every throttled request keeps calling for up to 60 s. Retried calls
compete with new requests for the same bucket, so new requests are throttled too and join the retry
pool. API Gateway gives up at 29 s (504) while the Lambda keeps retrying: the work is wasted, and the
portal retries once on 504/500/429, adding more load. Concurrency climbs to the reserved limit and
Lambda starts rejecting with 429. Only when base traffic drops below quota for long enough does the
backlog drain (~09:12). Bedrock invocations 6,684 -> 20,863 (x3.1) and throttles 532 -> 12,382 on
+20% user traffic.

## Red herrings

- **Reserved concurrency 100 -> 150.** Last Monday peaked at 41 concurrent executions; the limit
  never bound. This Monday it pinned at 150 only after requests started sitting in retry loops: an
  effect. The replay with your fix passes at 100 or 150.
- **Quota.** The quota did not change. A quota increase would hide the bug until the next wave; the
  fixed code on the same quota degrades ~150 requests in the one spike minute and is otherwise clean.

## Fix (see .grading/solution/)

- `SDK_RETRIES = {"total_max_attempts": 3, "mode": "standard"}`: the only retry layer, with jitter.
- `APP_POLICY = RetryPolicy(max_attempts=1, ...)`, retrying only transient codes with capped full
  jitter if anyone raises it later.
- `outcome_for_error`: ValidationException -> 400, transient -> 503 with `Retry-After: 30` (the
  portal shows "busy" and does not retry), anything else -> 500.

Equivalent alternative: SDK `total_max_attempts: 1` and the app layer doing up to 3-4 attempts with
full jitter. What matters: one layer, a small total, jitter, only transient errors.

Replay after the fix: error rate ~2.1% (all 503 in the 09:02 minute), p95 ~3.5 s, 1.06 calls per
request.

## Prevention

Alarm on `InvocationThrottles / Invocations` and on calls per request; load-test the login wave;
a review rule that names the retry layer and its total attempts for every outbound dependency;
remember standard mode's retry quota is per client (per Lambda execution environment), so it does not
protect the fleet; consider a cross-Region inference profile or more quota once the retries are sane.
