# Rubric: connect/ai-t1 The AI summary is missing and callers hear 8 seconds of silence
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: Connect stops waiting at the block's 8 s synchronous limit and takes the error branch while the Lambda (30 s timeout) keeps running and finishes "successfully"; the slow invocations are Bedrock ThrottlingException retries with SDK backoff (attempts=3, multi-second totalRetryDelay) plus long generations (maxTokens 2048, 500-1000 output tokens); throttling started when the analytics backfill began at 14:02 sharing the account's on-demand quota for the model. Partial (10-15): "Bedrock was slow" or "retries" without the Connect-timeout vs Lambda-success mechanism. Zero: memory, cold starts. |
| 3 | Evidence | 20 | Quotes trace timelines (429, backoff, 429, backoff, 200 past 8000 ms), the app log line with attempts/totalRetryDelayMs, Lambda Errors 0 vs flow log Error results, Bedrock InvocationThrottles rising at 14:00 with the backfill, and Duration max > 8000. |
| 4 | Red herring handled | 5 | Memory ruled out: memory used is steady across healthy and slow runs, time is spent waiting on the network/backoff, not CPU. |
| 5 | Fix quality | 10 | Deadline = min(flow budget, remaining time) minus safety, race with abort and cleanup, degraded result not exception, maxAttempts bounded or irrelevant under the deadline, maxTokens small, Timeout <= 8 s. |
| 6 | Production follow-ups | 10 | Concrete: separate quota or provisioned/cross-region inference profile for real-time vs batch (or throttle the backfill), async Lambda mode (up to 60 s, Wait + Load Lambda result) or generate the summary after transfer, a prompt that covers latency, alarm on Duration p99 vs the flow limit and on Bedrock throttles, degraded-rate metric. |
Total: 100
