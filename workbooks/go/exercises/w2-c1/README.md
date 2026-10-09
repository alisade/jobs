# go/w2-c1 albstats: a fuzz-tested ALB log parser with a concurrent aggregator

**Type:** coding | **Estimate:** 2.5 hours | **Week 2:** concurrency, context, testing (Mon-Thu)

## Scenario

Harbor Lane, a freight-tracking SaaS, ships ALB access logs to S3. During incidents the
SREs run a Python script over a few GB of gzipped logs to get per-target-group 5xx counts
and latency percentiles; it takes minutes and crashed last week on a carrier bot whose
User-Agent contained escaped quotes. You are replacing it with `albstats`, a Go CLI
(`cmd/albstats` is done) built on a parser and aggregator in package `alblog`.

## Task

1. Implement `ParseLine` and `Entry.Format` in `alblog/parse.go`.
2. Implement `Aggregate` in `alblog/aggregate.go`.
3. Add table rows and fuzz seeds for what you discover; run `make fuzz` for at least a
   minute and fix what it finds. Fill in `ANSWER.md`.

Types, sentinels and field names are fixed in `alblog/types.go`; do not change them.

## Requirements

### Parser

1. Fields are separated by single spaces. A field that starts with `"` runs to the next
   unescaped `"`, which must be followed by a space or end of line (`ErrMalformedQuote`
   otherwise, `ErrUnterminatedQuote` if there is none). Inside quotes, `\"` is a quote
   and `\\` a backslash. Any field may be quoted. A trailing `\r` is ignored.
2. A line needs at least `MinFields` (18) fields (`ErrTooFewFields`); later fields are
   ignored, because AWS keeps appending new ones.
3. `-` in a string field becomes `""`; `-` in a status code becomes 0. Status codes are
   100-599. Processing times are `-1` or a finite, non-negative number of seconds. Byte
   counts are non-negative integers (`-` is invalid). Time is RFC 3339, stored in UTC.
4. Every error is a `*ParseError` with `Line` = the `lineNo` argument, `Field` = the
   name from `FieldNames` (or `""` for tokenizer/field-count errors), wrapping one of the
   sentinels so `errors.Is` and `errors.As` work.
5. `Format` returns a line that `Parse` maps back to an equal `Entry`
   (`reflect.DeepEqual`). This is the fuzz invariant.

### Aggregator

6. `Aggregate(ctx, r, workers)` reads lines from `r` (lines can exceed 64 KiB), skips
   blank or whitespace-only lines, and parses with `workers` goroutines (`<= 0` means
   `GOMAXPROCS`). Only one goroutine reads `r`.
7. Per target group (`"-"` when there is none): request count, ELB 5xx, target 5xx, and
   nearest-rank P50/P99 of `TargetProcessing`, excluding `-1`, rounded to the nanosecond.
   `Groups` sorted by ARN.
8. Malformed lines are counted, not fatal. `FirstErrors` holds the errors with the lowest
   line numbers (at most `MaxErrors`), ascending. The report must be identical for any
   worker count.
9. A read error aborts the run and is returned wrapped. Cancelling `ctx` returns an error
   wrapping `context.Canceled` promptly, with no goroutines left behind.

## Acceptance criteria

- `make test` passes with `-race`; `make fuzz` runs 60s without failures.
- Hidden tests cover escapes, `-` values, trailing fields, UTC, typed errors per field,
  round-trip seeds, determinism across worker counts, exact percentiles, first-errors
  ordering, long lines, read errors, cancellation and goroutine leaks.

## How to run

```
make setup
make test
make fuzz FUZZTIME=2m
make run           # report for testdata/sample.log
```

## What to submit

`alblog/parse.go`, `alblog/aggregate.go`, any tests and fuzz corpus you added, and
`ANSWER.md`. Then `/grade go/w2-c1` from the workbooks root.

## Study-guide links

- Go Concurrency Patterns: Pipelines and cancellation: https://go.dev/blog/pipelines
- errgroup: https://pkg.go.dev/golang.org/x/sync/errgroup
- Go Fuzzing: https://go.dev/doc/security/fuzz/
- Go Wiki, table-driven tests: https://go.dev/wiki/TableDrivenTests
- ALB access log format: https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-access-logs.html
