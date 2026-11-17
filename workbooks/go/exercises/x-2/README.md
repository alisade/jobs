# go/x-2 A sharded TTL cache with load deduplication for registry lookups

**Type:** coding | **Estimate:** 2.5 hours | **Week 7 (add-on):** runtime and memory, code reading (workqueue/cache internals), API server at scale

## Scenario

Arclight's agent-fleet operator resolves each `MCPServer`'s registry entry (image digest,
allowed callers, tool manifest) from an internal registry API on every reconcile. At
4,000 objects with a 10-minute resync, plus bursts when the informer cache resyncs, the
registry rate-limits the operator (HTTP 429) and reconciles back up. You are adding an
in-process cache in front of the registry client: bounded memory, TTL freshness, no
thundering herd when 50 reconciles miss the same key at once, and no allocations on
the hit path because it runs on every reconcile.

## Task

Implement `ttlcache.Cache[K comparable, V any]` in `ttlcache/cache.go`. Keep the exported
names and signatures (`New`, `Get`, `Set`, `Delete`, `Len`, `GetOrLoad`, `Options`,
`Clock`, `LoaderFunc`); you may delete `ErrNotImplemented`. Fill in `ANSWER.md` with
your design and `make bench` numbers.

## Requirements

1. **Sharding:** `Options.Shards` rounded up to a power of two (default 16); each shard
   has its own lock. Hash any `comparable` key without allocating (hint: `hash/maphash`).
2. **TTL:** default 1 minute; an entry is expired when `now >= set time + TTL`. Time comes
   only from `Options.Clock` (wall clock when nil). `Set` overwrites and refreshes the TTL.
3. **Bound:** at most `MaxEntriesPerShard` (default 1024) per shard. Inserting a new key
   into a full shard evicts an expired entry if one exists, else the entry closest to
   expiry. The key just inserted is always present afterwards.
4. **GetOrLoad:**
   - concurrent callers for the same missing key share one loader call;
   - success is cached; an error goes to every waiter of that load and is not cached;
   - a waiter whose ctx is done returns `ctx.Err()` promptly, while the load continues
     for others and its ctx is not cancelled by that caller (it may keep ctx values);
   - loads for different keys run concurrently (never hold a shard lock while loading).
5. **Performance:** a `Get` hit performs zero allocations, for string and struct keys.
6. `-race` clean under mixed concurrent use. Zero-value `Options` must work.

## Acceptance criteria

- `make test` passes; `make bench` shows `0 allocs/op` for `BenchmarkGetHit`.
- Hidden tests cover TTL boundary, refresh, delete, defaults, eviction bound and policy,
  load deduplication, error sharing, waiter cancellation, concurrent loads of different
  keys, reload after expiry, a mixed-ops race test, and `testing.AllocsPerRun` on hits.

## How to run

```
make setup
make test      # visible tests (-race)
make bench
```

## What to submit

`ttlcache/cache.go` and `ANSWER.md`, then `/grade go/x-2`.

## Study-guide links

- A Guide to the Go Garbage Collector: https://go.dev/doc/gc-guide
- client-go util/workqueue (dedup and rate limiting in practice): https://github.com/kubernetes/client-go/tree/master/util/workqueue
- controller-runtime pkg/cache: https://github.com/kubernetes-sigs/controller-runtime/tree/main/pkg/cache
- EKS best practices, scalability: https://docs.aws.amazon.com/eks/latest/best-practices/scalability.html
