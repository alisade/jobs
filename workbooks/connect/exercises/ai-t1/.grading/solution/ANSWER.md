# ANSWER: connect/ai-t1 The AI summary is missing and callers hear 8 seconds of silence

## Approach

Compared flow logs (Results Error) with Lambda metrics (Errors 0): the Lambda succeeds after Connect gives
up. Then read the trace samples and the app log line for the slow invocations.

## Root cause

Connect's synchronous block waits 8 s; the function timeout is 30 s, so slow runs finish after Connect has
taken the error branch. Slow runs = ThrottlingException retries with SDK backoff plus long generations:

    trace ... total 9443 ms: Converse #1 HTTP 429, backoff +2795 ms, #2 HTTP 429, backoff +2795 ms, #3 200 +3349 ms
    {"msg":"converse ok","attempts":3,"totalRetryDelayMs":5590,"outputTokens":...}

Bedrock InvocationThrottles for the model jump from 0 to 412 at 14:00, when the analytics backfill (14:02)
started sharing the account's on-demand quota. Memory: usage is the same on fast and slow runs.

## Fix

Deadline min(6.5 s, remaining) - 300 ms with abort; DEGRADED answers (timeout/throttled/error) instead of
exceptions; maxAttempts 2; maxTokens 350; empty transcript short-circuit; Timeout 8 s. make test passes.

## Trade-offs / what I would do in production

Isolate batch from real-time capacity (separate account/quota or a cross-region inference profile for the
backfill), consider async Lambda mode or summarizing after transfer, play a short prompt while waiting,
alarm on Duration p99 > 6 s, Bedrock throttles and the degraded rate.
