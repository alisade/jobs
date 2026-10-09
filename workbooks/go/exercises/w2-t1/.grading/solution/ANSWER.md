# go/w2-t1 ANSWER (model)

## Approach

Started from the pager: OOMs cluster in the snapshot window when bulk latency spikes.
Raising the limit would only delay the kill, so I looked for what grows. `metrics.txt`
shows `go_goroutines` tracking `driftwood_send_timeouts_total` almost 1:1, while
`batches_sent` flattens. That pointed at timeouts creating goroutines that never exit.
Ran `make setup` and read `artifacts/goroutines-live.txt`, then `go tool pprof` style
grouping in the prod dump.

## Root cause

Goroutine leak in `sendOnce` (`shipper/shipper.go:116`). The result channel is unbuffered.
On timeout `sendOnce` returns via `<-ctx.Done()`; when the sink later returns, the
goroutine blocks forever on `result <- ...` because nothing will ever receive. Each leaked
goroutine keeps its closure alive, including the gzipped payload.

Evidence:
- prod dump: `15352 github.com/tidewater/driftwood/shipper.(*Shipper).sendOnce.func1()`,
  state `[chan send, 51 minutes]` at `shipper.go:116`.
- live repro: `goroutines before=1 after all Flush calls returned=425`, 424 at shipper.go:116.
- metrics: 02:55 `go_goroutines 15377`, `send_timeouts_total 15354`.
- heap: `inuse_space` top is `bytes.Clone` 163.9MB (retained payloads). The gzip entries are
  top in `alloc_space` (allocation churn), which the pool and GC keep bounded: red herring.

## Fix

`result := make(chan error, 1)`. The late result lands in the buffer and the goroutine
exits. Kept the goroutine (instead of calling Send inline) because the vendor client
ignores ctx and each attempt must stay bounded by SendTimeout. Verified: `make test`,
hidden-style leak test with `runtime.NumGoroutine`, and `make repro` now reports
`after=1`.

## Trade-offs / what I would do in production

- Bound in-flight sends with a semaphore; with a ctx-ignoring client, goroutines still
  live until the client's own timeout.
- goleak in CI; alert on goroutine growth; canary the DaemonSet through one snapshot window.
- Push the vendor to honour ctx, or set an `http.Transport` timeout under SendTimeout.
