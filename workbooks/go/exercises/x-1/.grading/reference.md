# Reference: go/x-1 labelgate regression

## Root cause

`router/router.go:102` in `Router.evaluate`:

```go
re := regexp.MustCompile(anchor(rule.Pattern))   // on every cache miss, for every rule tried
```

2.7.0 moved pattern "validation" into `New` but kept compiling in the hot path, so each
series that misses the decision cache compiles every candidate rule's regexp. Compiling
an RE2 program is hundreds of allocations (parse tree, program, onepass tables). With
high-cardinality `pod` labels the cache hit ratio is ~5% (grafana-export.txt), so almost
every series pays it. The allocation rate drives GC frequency and mheap lock contention,
which shows up as `runtime.*` time (mallocgc, gcBgMarkWorker, lock2, allocSpan) on top of
the compile itself.

## Evidence

- `go tool pprof -top -cum artifacts/cpu.pprof`: `regexp.MustCompile` / `regexp.compile`
  is the largest application-level node under `Router.evaluate`, which is the bulk of
  `Router.Route`.
- `go tool pprof -list 'Router..evaluate' artifacts/cpu.pprof`: the cost sits on the
  MustCompile line, not on MatchString.
- `go tool pprof -sample_index=alloc_space -top artifacts/heap.pprof`: regexp/syntax
  and regexp.compile dominate allocations.
- `inuse_space` shows `decisionCache.put`, `maps.clone`, `strings.Builder` (the cache
  key) at the top: that is the bounded 50k-entry cache, retained by design. It explains
  part of the RSS increase, not the CPU or latency: red herring.
- `BenchmarkRouteCacheMiss`: ~460 allocs/op before, ~16 after. loadprofile on the
  author's machine: p99 72ms -> 8ms, throughput ~3.5x.

## Fix

Compile once in `New`, store the compiled matcher next to the rule
(`compiledRule{Rule, re *regexp.Regexp}`), and call `rule.re.MatchString` in the hot path.
`*regexp.Regexp` is safe for concurrent use. See `.grading/solution/router/router.go`.

## Production notes

- Allocation-aware benchmarks in CI (`-benchmem`, benchstat against main) catch this
  class of regression before release.
- Continuous profiling lets you diff 2.6 vs 2.7 profiles directly (`-diff_base`).
- Re-evaluate the cache: at a 5% hit ratio it costs memory and a key build per series.
- PGO with a production CPU profile is a cheap 2-7% once the hot path is sane.
