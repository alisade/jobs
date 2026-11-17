# Reference: go/w1-c1 snapshot-janitor

The reference implementation is in `.grading/solution/janitor/janitor.go` and
`.grading/solution/cmd/snapshot-janitor/main.go`.

## Key decisions

- **Interface at the consumer.** `EC2API` lists only the two calls used. `*ec2.Client`
  satisfies it implicitly, and because it has `DescribeSnapshots` it also satisfies
  `ec2.DescribeSnapshotsAPIClient`, so the SDK paginator works against the fake too.
- **Classify, then sort, then act.** Listing and deleting are separate phases, so "oldest
  first" and the cap are exact and testable.
- **Error codes via `errors.As(err, &smithy.APIError)`.** The SDK wraps API errors in
  `*smithy.OperationError` and `*http.ResponseError`; `errors.As` walks the chain.
  Matching on `err.Error()` breaks when the message format changes.
- **Partial failure.** `errors.Join(ErrPartialFailure, err1, err2, ...)` gives callers both a
  stable sentinel for exit codes and every root cause for logs. `errors.Is` matches any
  member of a joined error.
- **Cancellation.** Check `ctx.Err()` before each delete and treat `context.Canceled` from the
  SDK as fatal, not as a per-snapshot failure.
- **Nil safety.** Every SDK field is a pointer; `aws.ToString`, `aws.ToTime`, `aws.ToBool`
  avoid panics on sparse responses.
- **Behaviour change vs Python worth calling out:** `--max-deletes` counts successful
  deletes only (an in-use skip does not consume the budget), and an empty owner id is
  rejected instead of listing public snapshots.

## Production notes a strong answer mentions

- IAM: `ec2:DescribeSnapshots` plus `ec2:DeleteSnapshot` scoped with conditions (resource
  tags / `ec2:Owner`), granted through EKS Pod Identity to a dedicated service account.
- CronJob: `concurrencyPolicy: Forbid`, `startingDeadlineSeconds`, `backoffLimit`,
  `activeDeadlineSeconds`, `terminationGracePeriodSeconds` long enough to finish an
  in-flight delete.
- SDK retries: the default retryer handles `RequestLimitExceeded`; consider
  `retry.AddWithMaxAttempts` and adaptive mode for big accounts.
- Observability: emit deleted/skipped/failed counts as metrics (or log-based metrics) and
  alert on exit code 1; run dry-run in a new account first.
