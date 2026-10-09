# Reference: go/w2-c1 albstats

Reference code: `.grading/solution/alblog/parse.go` and `.grading/solution/alblog/aggregate.go`.

## Parser

- A byte-level tokenizer: unquoted tokens end at the next space; quoted tokens unescape
  `\"` and `\\` and must be followed by a space or end of line. `strings.Fields` and
  `encoding/csv` both get ALB quoting wrong.
- A small `fieldParser` records the first error (the "errWriter" pattern from "Errors are
  values"), so the field mapping reads as a straight list instead of 18 `if err != nil`.
- `*ParseError{Line, Field, Err}` with `Unwrap`, wrapping a sentinel via `%w`, so callers
  can use `errors.As` for location and `errors.Is` for the class.
- What fuzzing finds in a first-draft parser: `NaN`/`Inf` latencies (DeepEqual fails on
  NaN), quotes or spaces in fields that are normally unquoted (Format must quote them),
  empty values (Format must write `-`), and times like `0000-01-01T00:00:00+01:00` that
  become year -1 in UTC and cannot be formatted back as RFC 3339.

## Aggregator

- One producer goroutine owns the `bufio.Scanner` (buffer raised to 1 MiB) and sends
  batches of 256 lines on a channel with capacity `workers`: bounded memory, cheap
  channel overhead, natural back-pressure.
- Workers keep private partials (no locks), merged after `g.Wait()`. Determinism comes
  from merging by key, sorting latencies before percentiles, and sorting errors by line.
- `errgroup.WithContext`: a read error or cancellation cancels the derived context; every
  send selects on `ctx.Done()`, workers check `ctx.Err()` per batch, and `close(jobs)` in
  the producer's defer guarantees workers exit, so nothing leaks.
- Nearest-rank percentile: `rank = ceil(p/100 * n)`, value `sorted[rank-1]`.

## Production notes

- Exact percentiles hold every latency in memory (8 bytes per request per group); for
  multi-GB inputs use an HDR histogram or t-digest per worker and merge.
- Stream straight from S3 with `gzip.NewReader`; parallelise across objects, not only lines.
- For ad-hoc questions over weeks of logs, Athena over the partitioned ALB table is cheaper
  than any CLI.
