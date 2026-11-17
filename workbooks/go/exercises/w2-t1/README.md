# go/w2-t1 driftwood: log shipper pods OOMKilled every night

**Type:** troubleshooting | **Estimate:** 2 hours | **Week 2:** concurrency, context, profiling (Tue context/sync, Wed memory model and profiling)

## Scenario

Tidewater Analytics runs `driftwood`, a Go log shipper, as a DaemonSet on every node of
its production EKS clusters. It gzips batches of log lines and posts them to the
OpenSearch bulk endpoint. Since v1.14.0 rolled out, pods are OOMKilled at 256Mi, mostly
during the nightly OpenSearch snapshot window, leaving holes in tenant dashboards. The
incident channel wants to raise the memory limit to 1Gi and blames the new gzip buffer
pool.

## What you get

- `artifacts/PAGER.txt` - the page and on-call notes. Start here.
- `artifacts/kubectl-describe-pod.txt`, `artifacts/metrics.txt`, `artifacts/heap-top.txt`,
  `artifacts/goroutines-prod-excerpt.txt`, `artifacts/CHANGELOG-excerpt.md` - collected in prod.
- `artifacts/goroutines-live.txt` - produced by `make setup`: a real goroutine profile from
  running this code against a slow fake bulk endpoint (`cmd/repro`).
- The source: `shipper/shipper.go` (core), `cmd/driftwood` (binary), `cmd/repro`.

## Task

1. Find the root cause. Do not just raise the limit.
2. Fix it in `shipper/` with the smallest correct change, keeping every documented
   behaviour (see below).
3. Write `ANSWER.md`: root cause with evidence (file:line, profile and metric excerpts),
   the fix, how you verified it, and what you would change in production.

## Behaviour that must be preserved

- `Flush` delivers every line, newline-delimited and gzipped, in one `Send` per attempt.
- Each attempt is bounded by `SendTimeout` **even when the sink ignores ctx** (the vendor
  client does), and returns an error wrapping `context.DeadlineExceeded` on timeout.
- Retries with exponential backoff up to `MaxRetries`; parent ctx cancellation stops retries.
- `Stats` counters stay accurate; `Shipper` stays safe for concurrent use (`-race` clean).

## Acceptance criteria

- `make test` passes; `make repro` shows goroutines returning to baseline after the brownout.
- Hidden tests: goroutine count returns to baseline after timeouts (sink that ignores ctx,
  sink that honours ctx, parent cancel, sustained brownout), retries, timeouts, -race.
- `ANSWER.md` names the leaking line and explains why the heap profile pointed at gzip.

## How to run

```
make setup     # build + reproduce into artifacts/goroutines-live.txt
make test      # visible tests (-race)
make repro     # re-run the reproduction after your fix
```

## What to submit

Your fix in `shipper/` and a completed `ANSWER.md`, then `/grade go/w2-t1`.

## Study-guide links

- Go Concurrency Patterns: Context: https://go.dev/blog/context
- Go Concurrency Patterns: Pipelines and cancellation: https://go.dev/blog/pipelines
- Diagnostics (profiling, goroutine dumps): https://go.dev/doc/diagnostics
- net/http/pprof: https://pkg.go.dev/net/http/pprof
- 100 Go Mistakes (concurrency section): https://100go.co/
