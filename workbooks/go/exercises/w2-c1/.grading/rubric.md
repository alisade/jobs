# Rubric: go/w2-c1 albstats: a fuzz-tested ALB log parser with a concurrent aggregator
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Concurrency design | 15 | Full: single reader goroutine, bounded channel (back-pressure), fixed worker count, per-worker partial results merged after `Wait` (no shared map behind a mutex in the hot path), every channel send also selects on `ctx.Done()`, `errgroup.WithContext` or equivalent so the first error cancels the rest, deterministic merge. Partial: correct but a goroutine per line, an unbounded buffer, or a global mutex. Zero: races or leaks. |
| 3 | Parser and error design | 10 | Full: hand-written tokenizer (not `encoding/csv` hacks or a regex that cannot express escapes), one `*ParseError` type wrapping sentinels, field names from `FieldNames`, careful numeric validation (NaN/Inf, -1 only). Partial: works but errors are strings or lose the field. Zero: panics on bad input. |
| 4 | Testing craft | 15 | Full: added table rows for every rule, extra fuzz seeds, ran `make fuzz` and reports what it found (e.g. NaN, years outside 0-9999 after UTC conversion, quoting in unquoted positions) with the regression seed committed under `alblog/testdata/fuzz`. Partial: a few extra rows, no fuzz findings. Zero: only the given tests. |
| 5 | ANSWER.md and production judgement | 10 | Full: memory of exact percentiles vs t-digest/HDR histograms, gzip/S3 streaming, why batching beats a channel send per line, when Athena is the better tool. Partial: generic. Zero: empty. |
Total: 100
