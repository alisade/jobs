# Reference: go/w2-t1 driftwood goroutine leak

## Root cause

`shipper/shipper.go:113-121`, `sendOnce`:

```go
result := make(chan error)          // unbuffered
go func() { result <- s.sink.Send(ctx, payload) }()
select {
case err := <-result: return err
case <-ctx.Done():    return ctx.Err()   // nobody will ever read result again
}
```

When an attempt times out, `sendOnce` returns through the `ctx.Done()` branch. Later the
sink returns (the vendor client after its own 30s timeout, or immediately for a
ctx-aware sink) and the goroutine blocks forever on the unbuffered send. Each leaked
goroutine pins its closure, including the gzipped `payload` (`bytes.Clone`), so inuse
heap grows with the number of timeouts. Nightly OpenSearch snapshots push bulk latency
above `SendTimeout` (5s), timeouts spike, goroutines and heap climb to the 256Mi limit.

Evidence trail:
- `metrics.txt`: `go_goroutines` = `driftwood_send_timeouts_total` + ~23 at every sample.
- `goroutines-prod-excerpt.txt`: 15,352 goroutines `[chan send, 51 minutes]` at
  `shipper.go:116`, created by `sendOnce`.
- `make setup` live profile: N goroutines parked at `shipper.go:116` after every Flush
  returned and every sink call finished.
- `heap-top.txt`: `alloc_space` is dominated by gzip (churn, bounded by the pool and GC);
  `inuse_space` is dominated by `bytes.Clone` - retained payloads, i.e. something holds
  references. The pool is a red herring.

## Fix

```go
result := make(chan error, 1)
```

The late send now completes into the buffer and the goroutine exits; the channel is
garbage collected. Calling `Send` synchronously would also stop the leak but breaks the
documented guarantee that each attempt is bounded by `SendTimeout` when the sink ignores
ctx (hidden test `TestHiddenTimeoutBoundsEachAttempt`).

## Production notes

- Even fixed, a ctx-ignoring client keeps one goroutine per timed-out attempt alive until
  the client's own timeout fires. Bound in-flight attempts with a semaphore and set the
  vendor client's transport timeout below SendTimeout x retries.
- Add `go.uber.org/goleak` to tests; alert on `go_goroutines` slope, not just memory.
- DaemonSet rollouts: canary a node group first; watch goroutines and RSS through one
  snapshot window before fleet-wide rollout.
