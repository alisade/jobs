# go/w2-c1 ANSWER (model)

## Approach

Wrote the table first from the ALB docs (quoted fields, `-` semantics, -1 latencies), then
a byte-level tokenizer and a `fieldParser` that keeps the first error. Ran `make fuzz` for
5 minutes; it found NaN latencies, a `"` inside the type field, and a year -1 after UTC
conversion. Each became a seed in `alblog/testdata/fuzz/FuzzParse` and a validation rule.

## Fix

- `parse.go`: tokenizer, `ParseLine`, `Format` (quotes any value with a space, quote or
  backslash; writes `-` for empty strings).
- `aggregate.go`: one reader goroutine, batches of 256 lines on a channel bounded to the
  worker count, per-worker partials merged after `errgroup.Wait`, sorted output.
- Cancellation: every send selects on `ctx.Done()`; the producer closes the channel in a
  defer; tests show no goroutines left.

## Trade-offs / what I would do in production

- Exact percentiles are memory-bound; switch to per-worker HDR histograms merged at the end.
- Read gzip objects from S3 concurrently (one producer per object).
- For anything beyond incident triage, query the Athena ALB table instead.
