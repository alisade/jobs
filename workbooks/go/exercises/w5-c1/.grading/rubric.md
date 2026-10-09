# Rubric: go/w5-c1 Trace agent tasks across Kafka with OpenTelemetry and franz-go
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 55 | points = 55 * passed / total from grade.sh |
| 2 | Propagation correctness | 15 | Full: inject happens after the PRODUCER span starts (header names that span), extract is onto the caller ctx, Set replaces instead of appending, no globals mutated, sane nil defaults. Partial: works in tests but e.g. extracts onto `context.Background()` or relies on the global propagator. Zero: headers appended blindly or trace broken. |
| 3 | Instrumentation quality | 10 | Full: semconv constants used (not hand-typed keys), span kinds right, `defer span.End()`, error recorded + status + `error.type`, attributes cheap and low-cardinality (no payloads or keys as attributes). Partial: some missing. Zero: spans leak or never end. |
| 4 | Idiomatic Go | 5 | Full: small value-receiver carrier, nil-safe, no needless allocations or goroutines, clear package doc. Partial: works but awkward. |
| 5 | ANSWER.md and production judgement | 15 | Full: justifies child vs link and explains when links win (batch, fan-in), plus 2-3 concrete production points (kotel plugin vs hand-rolled, tail sampling in the collector, header size/PII in baggage, consumer lag vs span latency). Partial: generic. Zero: empty. |
Total: 100
