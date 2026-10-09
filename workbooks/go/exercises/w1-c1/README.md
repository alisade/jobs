# go/w1-c1 Port snapshot-janitor from Python to idiomatic Go

**Type:** coding | **Estimate:** 2 hours | **Week 1:** Go language and idioms (Thu errors, Weekend port a tool)

## Scenario

Northwind Freight's platform team runs `legacy/snapshot_janitor.py` nightly from a
Jenkins box to delete expired EBS snapshots in the platform account. The Jenkins box is
being decommissioned. The replacement is a static Go binary that runs as a Kubernetes
CronJob on EKS with Pod Identity. Last quarter the Python script deleted a snapshot that
backed a golden AMI and once exited 0 after half its deletes were throttled, so the
reviewers want the error handling in the Go version to be explicit and testable.

## Task

1. Implement `janitor.Run` in `janitor/janitor.go` against the small `EC2API` interface
   (the real `*ec2.Client` satisfies it; tests use a fake). Do not change the exported
   names or signatures; the hidden tests use them.
2. Finish `cmd/snapshot-janitor/main.go`: flags, JSON `slog`, SIGTERM handling, exit codes.
3. Fill in `ANSWER.md`.

## Requirements

1. List with `DescribeSnapshots` filtered to `OwnerIds = [cfg.OwnerID]`, following every
   page (use `ec2.NewDescribeSnapshotsPaginator`). An empty `OwnerID` is a config error:
   return an error before calling AWS.
2. Skip, and record in `Result.Skipped`:
   - snapshots tagged `<KeepTag>=true` (value case-insensitive; `KeepTag` defaults to `retain`) as `ReasonRetained`;
   - snapshots whose description starts with `Created by CreateImage(` as `ReasonAMI`.
3. Ignore (do not record) snapshots whose `StartTime` is not older than `Now - RetentionDays`.
4. Delete candidates oldest first. `DryRun` is passed through to `DeleteSnapshot`; the
   API error code `DryRunOperation` means "would have succeeded" and counts as deleted.
5. `InvalidSnapshot.InUse` is a skip (`ReasonInUse`), not a failure.
6. `MaxDeletes > 0` caps successful (or would-be) deletions per run; the rest are skipped as
   `ReasonMaxDeletes`.
7. Any other delete error is recorded in `Result.Failed` and the run continues. At the end,
   return an error for which `errors.Is(err, ErrPartialFailure)` is true **and**
   `errors.Is`/`errors.As` still find each underlying AWS error.
8. A `DescribeSnapshots` failure aborts the run with the cause wrapped (`%w`), and is not a
   partial failure.
9. Context cancellation (SIGTERM from the kubelet) stops further deletes promptly and
   returns an error wrapping `context.Canceled`.
10. Map AWS error codes with `errors.As` into `smithy.APIError`, not string matching on
    `err.Error()`.

## Acceptance criteria

- `make test` passes and `go vet ./...` is clean.
- Hidden tests cover pagination, tags, AMI protection, retention boundary, dry run, in-use,
  partial failure wrapping, the cap, describe failure, cancellation and bad config.
- `main.go` exits 0 / 1 (`ErrPartialFailure`) / 2 (anything else).

## How to run

```
make setup     # go mod download + build
make test      # visible tests (-race)
make build     # bin/snapshot-janitor
```

No AWS account is needed; nothing in the tests calls AWS.

## What to submit

Your edits to `janitor/janitor.go`, `cmd/snapshot-janitor/main.go` and `ANSWER.md`, then
run `/grade go/w1-c1` from the workbooks root.

## Study-guide links

- Working with Errors in Go 1.13: https://go.dev/blog/go1.13-errors
- `errors` package (`Join`, `Is`, `As`): https://pkg.go.dev/errors
- AWS SDK for Go v2, handling errors: https://docs.aws.amazon.com/sdk-for-go/v2/developer-guide/handle-errors.html
- AWS SDK for Go v2, unit testing with interfaces: https://docs.aws.amazon.com/sdk-for-go/v2/developer-guide/unit-testing.html
- Structured logging with slog: https://go.dev/blog/slog
