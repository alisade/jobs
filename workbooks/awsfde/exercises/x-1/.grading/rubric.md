# Rubric: awsfde/x-1 Idempotent document-ingestion Lambda
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Idempotency design | 15 | Full: conditional write before the side effect, clientToken derived from the object version, PENDING/STARTED states so a crash between the call and the update is safe, consistent read on the duplicate check. Partial: dedupe only on messageId (different messages can carry the same event) or only in memory. |
| 3 | Failure classification | 10 | Full: poison vs transient clearly separated; poison recorded with the reason for inspection; transient failures reported per record so the rest of the batch is not redelivered. Partial: raises for the whole batch, or drops transient failures. |
| 4 | Tenant safety | 5 | Tenant only from the validated key prefix and an active registry entry; path traversal and sidecars rejected. |
| 5 | Operations (ANSWER.md) | 20 | Full: ReportBatchItemFailures on the event source mapping, visibility timeout at least six times the function timeout, maxReceiveCount and a DLQ alarm with a redrive procedure, maximum concurrency to protect Bedrock, one sync per data source so coalescing per tenant (debounce or Step Functions) is better at scale, TTL on job records. Partial: some. |
Total: 100
