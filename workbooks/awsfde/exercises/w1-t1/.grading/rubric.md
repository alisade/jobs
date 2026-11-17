# Rubric: awsfde/w1-t1 Throttling storm after the resilience release
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: stacked retry layers: botocore `max_attempts=10` means 10 retries (11 attempts) per SDK call, wrapped in an app loop of 5 attempts with a fixed 1 s delay and no jitter that also retries ValidationException, so one request can make up to 55 calls (capped in practice by the 60 s Lambda timeout, ~20); the extra load during the 09:02 wave keeps the token bucket empty, the API Gateway 29 s timeout returns 504 while the Lambda keeps calling Bedrock (wasted work), and the portal's single retry on 5xx adds more load, so the overload outlives the spike (metastable). Partial (10-15): "too many retries" without the multiplication, the max_attempts semantics or why it persisted. Zero: blames quota, traffic growth or concurrency. |
| 3 | Evidence | 20 | Full: at least two independent pieces quoted: dashboard rows (bedrock_inv and throttles per minute, both Mondays), a requests.log line with model_calls ~20 and its attempt list, ValidationException requests making 5 calls, the `meta.config.retries` output showing total_max_attempts 11. Partial: one piece, or numbers without commands. |
| 4 | Red herrings handled | 5 | Explains why reserved concurrency 100 -> 150 is an effect, not a cause (last Monday peaked at 41 concurrent; concurrency only pinned at 150 once requests sat in retry loops) and why a quota increase alone would not fix it. |
| 5 | Fix quality | 10 | One retry layer, total attempts <= 4, full jitter with a cap, only transient codes retried, 503 + Retry-After on exhausted throttling, 400/500 mapping; no change to replay/ or evidence/. |
| 6 | Prevention / production | 10 | Concrete: alarm on InvocationThrottles/Invocations ratio and on calls per request, retry budget or circuit breaker across the fleet, load test of the login wave in CI or staging, review checklist for retry layers (SDK config semantics), cross-Region inference profile or provisioned throughput if demand really exceeds quota. Partial: generic. |
Total: 100
