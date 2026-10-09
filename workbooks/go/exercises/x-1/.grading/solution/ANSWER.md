# go/x-1 ANSWER (model)

## Approach

Ran `make setup` and started with `go tool pprof -top -cum artifacts/cpu.pprof` to see where
application time accumulates, then `-list` on the router, then compared heap
`alloc_space` vs `inuse_space`. Checked the release notes against what the profile shows.

## Root cause

`router/router.go:102`: `regexp.MustCompile(anchor(rule.Pattern))` inside `Router.evaluate`
runs on every cache miss for every rule tried. The cache hit ratio is ~5% because pod
names have random suffixes, so nearly every series compiles several regexps.

Evidence (author's run):
- `-top -cum`: `Router.Route` 27.8%, `Router.evaluate` 20.5%, `regexp.MustCompile` 18.9%.
  Most of the remaining runtime time is mallocgc / mheap.allocSpan / lock2 / GC workers,
  i.e. the cost of that allocation rate.
- `BenchmarkRouteCacheMiss`: 462 allocs/op before.
- `inuse_space` top is `decisionCache.put` / `maps.clone` / `strings.Builder`: the bounded
  cache. It is retained memory by design (and part of the RSS rise), not CPU: red herring.

## Fix

Compile once in `New` into `compiledRule{Rule, re}` and use `rule.re.MatchString`. After:
16 allocs/op on a miss; loadprofile p99 72ms -> 7.8ms, throughput 1458 -> 5258 req/s.
`go tool pprof -top -diff_base artifacts/cpu.pprof artifacts/cpu-after.pprof` shows
regexp.compile gone.

## Trade-offs / what I would do in production

- `-benchmem` benchmarks with a benchstat gate in CI.
- Continuous profiling and a canary with an SLO burn alert before full ArgoCD sync.
- Reconsider the cache at a 5% hit ratio; it costs ~90MiB per pod.
