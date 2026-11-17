# Reference: go/x-2 sharded TTL cache

Reference implementation: `.grading/solution/ttlcache/cache.go`.

## Design

- `shards []*shard`, power-of-two count, index = `maphash.Comparable(seed, key) & mask`.
  `maphash.Comparable` (Go 1.24+) hashes any comparable key without allocating.
- Shard: `sync.RWMutex`, `items map[K]entry[V]` where `entry` holds the value and an
  `int64` expiry in unix nanos (cheap compare, no time.Time in the map), and
  `inflight map[K]*call[V]`.
- `Get`: read clock, RLock, map lookup, RUnlock, compare. No allocation.
- Eviction on insert into a full shard: scan for an expired entry (return early) else the
  smallest expiry. O(n) per eviction at n <= 1024 is acceptable; at larger n use a
  min-heap keyed by expiry or a CLOCK/LRU list.
- `GetOrLoad`: fast-path `Get`; under the write lock re-check, then join or create the
  in-flight `call` (a `done` channel plus result fields). The loader runs in its own
  goroutine with `context.WithoutCancel(ctx)` so one caller cancelling does not cancel
  the shared load, and each waiter `select`s on `call.done` vs its own `ctx.Done()`.
  On completion the loader goroutine removes the in-flight entry and stores the value
  under the lock only on success, then closes `done` (the close publishes the result
  fields to waiters: happens-before via channel close).
- `x/sync/singleflight` with `DoChan` is an acceptable alternative if the learner keys it
  by a string; note it cannot take generic keys directly and `Forget` semantics matter.

## Things a strong answer mentions

- Loader panics: recover in the load goroutine and turn it into an error, or waiters hang.
- Detached loads still need a bound: wrap with `context.WithTimeout` inside the loader
  goroutine so a hung registry does not pin an in-flight entry forever.
- Negative caching (404) with a short TTL; stale-while-revalidate during registry outages.
- Metrics: hits, misses, loads, load errors, evictions, in-flight gauge.
- Memory: entry size x shards x max; the operator's container limit and GOMEMLIMIT.
