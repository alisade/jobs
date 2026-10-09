# Rubric: go/w2-t1 driftwood: log shipper pods OOMKilled every night
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 30 | Full: goroutine leak in `sendOnce` (shipper.go:116): unbuffered result channel, so after `sendOnce` returns on `ctx.Done()` the sender goroutine blocks forever on `result <- ...`, pinning its closure (the payload) - which is why inuse heap is `bytes.Clone`. Partial (12): "goroutine leak" without the mechanism or line. Zero: blames the sync.Pool / gzip, GOMEMLIMIT, or the memory limit. |
| 3 | Evidence | 20 | Full: cites at least two of: go_goroutines tracking send_timeouts_total in metrics.txt; 15k goroutines in `[chan send]` at shipper.go:116 in the prod dump; the live profile from `make setup`; inuse vs alloc heap distinction. Explains why the gzip red herring is bounded churn (alloc_space) not retention (inuse_space). Partial: one piece. Zero: none. |
| 4 | Fix quality | 10 | Full: minimal and correct (buffered channel of 1, or equivalent that keeps the SendTimeout bound when the sink ignores ctx); no behaviour regressions; verified with `make repro` before/after. Partial: works but over-engineered or drops the timeout guarantee for ctx-ignoring sinks. Zero: raises limits or adds a goroutine cap only. |
| 5 | Production judgement | 10 | Full: 2-3 concrete points, e.g. goleak in tests, alert on go_goroutines growth / ratio to timeouts, bound in-flight sends (semaphore) since a ctx-ignoring client can still pile up goroutines for its own timeout, fix the vendor client or wrap with a transport-level timeout, canary DaemonSet rollout (maxUnavailable). Partial: generic. Zero: none. |
Total: 100
