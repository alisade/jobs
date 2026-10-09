# go/x-2 ANSWER (model)

## Approach

Sharded map with a power-of-two shard count and `maphash.Comparable` for alloc-free
hashing of any comparable key. Each shard has an RWMutex, an items map with int64 expiry,
and an in-flight map of shared loads. GetOrLoad joins an existing in-flight call or starts
one in its own goroutine with `context.WithoutCancel`, then each caller waits on
`done` or its own ctx.

## Fix

`ttlcache/cache.go`. Benchmarks (M-series laptop): GetHit 39 ns/op 0 allocs,
GetParallel 22 ns/op 0 allocs, GetOrLoadParallel 231 ns/op 0 allocs.

## Trade-offs / what I would do in production

- Eviction is an O(n) scan per insert into a full shard; fine at 1024/shard, use a heap
  or CLOCK list beyond that.
- Recover loader panics into errors; put a timeout on detached loads.
- Negative-cache 404s briefly; serve stale on registry 5xx with a max staleness.
- Export hit ratio, load latency, evictions; size MaxEntriesPerShard from the pod limit.
