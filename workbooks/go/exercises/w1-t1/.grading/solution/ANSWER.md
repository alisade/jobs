# go/w1-t1 ANSWER (model)

## Approach

Correlated the Grafana deploy marker (13:58, v1.14.0) with the first `validation failed:
<nil>` log line (14:07). The curl transcript ruled out the omitempty change (500 also with
a description) and showed invalid flags still get 422, so the failure is specific to the
valid path. Reproduced with `make test` (TestPutValidFlagReturns200: status 500).

## Root cause

`validate` in `internal/flags/flags.go` declares `var verr *ValidationError` and ends with
`return verr` in a function whose result type is `error`. For a valid flag that returns an
interface holding (type `*ValidationError`, value nil), which is non-nil. Evidence:

```
$ cat > /tmp/x_test.go  # in package flags
err := validate(Flag{Key: "checkout-v2", Owner: "a@b.c", Env: "prod", Enabled: true, Rollout: 10})
t.Logf("%T %v nil=%v", err, err, err == nil)
--- x_test.go:9: *flags.ValidationError <nil> nil=false
```

`Service.Put` therefore wraps it as `validation failed: %w`; fmt prints `<nil>` for the
nil receiver (matching the prod log). The handler's `errors.As` matches the nil pointer,
`FieldErrors()` returns nil, so `fail()` falls through to the 500 branch.

## Fix

Return a literal `nil` when no field failed (`if verr == nil { return nil }`). Verified:
`make test` passes, `make repro` returns 200 for the valid PUT and 422 with four fields for
the invalid one. Kept omitempty and all-fields reporting.

## Trade-offs / what I would do in production

- Roll forward with the one-line fix rather than roll back (rollback loses the campaign
  feature); canary one replica first.
- Add a happy-path PUT test; enable `nilness` and `staticcheck` in CI.
- Team rule: functions return `error`, never a concrete error pointer variable that may be nil.
- Alert on PUT 5xx rate per route, tied to Argo Rollouts analysis for auto-abort.
