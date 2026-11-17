# Rubric: go/x-1 labelgate: CPU and p99 tripled after a release
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 25 | points = 25 * passed / total from grade.sh |
| 2 | Root cause identified | 30 | Full: `regexp.MustCompile` inside `Router.evaluate` (router/router.go:102) compiles every rule pattern on every cache miss; the cache hit ratio is ~5% so nearly every series pays it; the allocation churn also drives GC and mheap lock contention, which is the runtime.* time in the CPU profile. Partial (12): "regex is slow" without the per-request compile mechanism, or blames GC without tracing it to its allocation source. Zero: blames the decision cache, JSON, or GOMAXPROCS. |
| 3 | pprof evidence | 25 | Full: quotes `-top -cum` (or `-list`/`-peek`) lines showing regexp.compile under Router.evaluate with its share; distinguishes alloc_space (churn from compile) from inuse_space (the bounded cache, ~tens of MB, retained by design); before/after numbers from `make profile` or `make bench` (allocs/op ~460 to ~16). Partial: one profile view only, or no before/after. Zero: no profiler output. |
| 4 | Fix quality | 10 | Full: compile once in `New` and store the `*regexp.Regexp` with the rule (safe for concurrent use); validation and error naming preserved; no locking added to the hot path. Partial: a lazily-filled map/sync.Map of compiled patterns (works, but adds a lookup and hides config errors) or removal of the cache as well. Zero: no fix or semantics broken. |
| 5 | Production judgement | 10 | Full: 2-3 concrete points, e.g. benchmark with allocs in CI and benchstat gate, continuous profiling (Pyroscope/Parca) to compare releases, PGO from a prod profile, canary + SLO burn alert before full sync, reviewing whether the cache earns its memory given a 5% hit rate. Partial: generic. Zero: none. |
Total: 100
