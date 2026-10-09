# go/w1-c1 ANSWER (model)

## Approach

Read the Python script and wrote down its behaviour as a table of cases (retained, AMI,
young, candidate, dry run, in use, other error), then turned each into a test against a
fake `EC2API` before writing `Run`. Kept the two-phase flow (classify, then delete oldest
first). Changed two things deliberately: an empty owner id is now an error, and the
delete cap counts only successful deletes.

## Fix

- `janitor.Run`: SDK paginator over `DescribeSnapshots` with `OwnerIds`; classification
  switch; `slices.SortStableFunc` by `StartTime`; delete loop that maps API codes with
  `errors.As` into `smithy.APIError`; `errors.Join(ErrPartialFailure, ...)` at the end.
- Cancellation checked before each delete; SDK cancellation errors abort the run.
- `main.go`: flags, JSON slog, `signal.NotifyContext`, exit 0/1/2.

## Trade-offs / what I would do in production

- Pod Identity role limited to describe + delete with an owner condition.
- CronJob with `concurrencyPolicy: Forbid` and a grace period longer than one delete.
- Push deleted/failed counters to Prometheus via a Pushgateway or log-based metric; page on
  repeated exit 1.
- Deletes are sequential: at 200/run that is fine; for thousands, a small bounded worker
  pool with the adaptive retryer.
