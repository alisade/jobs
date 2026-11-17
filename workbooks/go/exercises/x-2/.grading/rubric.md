# Rubric: go/x-2 A sharded TTL cache with load deduplication for registry lookups
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 55 | points = 55 * passed / total from grade.sh |
| 2 | Concurrency design | 15 | Full: per-shard RWMutex (or equivalent) with no lock held across the loader call; in-flight map keyed per shard with a done channel (or x/sync/singleflight used correctly with DoChan); loader ctx detached via `context.WithoutCancel`; waiters select on done vs ctx.Done(). Partial: correct but one global lock, or a loader ctx tied to the first caller. Zero: races or deadlocks. |
| 3 | Performance and memory | 10 | Full: maphash.Comparable (or equivalent) for alloc-free hashing, int64 expiry, no closures or interface boxing on the hit path, `make bench` numbers reported; eviction cost discussed (O(n) scan vs heap/list). Partial: hits allocate or no numbers. Zero: no attention to the hot path. |
| 4 | Idiomatic generic Go | 5 | Full: clean type parameters, zero-value Options defaults, unexported internals, doc comments. Partial: `any` where a type parameter belongs, exported internals. Zero: reflection or interface{} values. |
| 5 | ANSWER.md and production judgement | 15 | Full: design rationale plus 2-3 concrete points, e.g. loader panic handling (waiters must not hang), negative caching of 404s with a short TTL, stale-while-revalidate to ride out registry outages, metrics (hit ratio, load latency, evictions), memory sizing per entry, when to choose an existing library (ristretto/otter) instead. Partial: generic. Zero: empty. |
Total: 100
