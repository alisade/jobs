# Reference: go/w5-c1 taskbus tracing

Reference files: `.grading/solution/tracing/carrier.go` and `.grading/solution/tracing/tracing.go`.

## Key points

- **Order matters in the producer.** Start the PRODUCER span first, then
  `Inject(ctx, carrier)` with the ctx returned by `Start`. Injecting the caller's ctx makes
  the consumer a sibling of the producer span instead of its child.
- **`Set` replaces.** Kafka headers are a list and allow duplicate keys. Appending on every
  produce leaves stale `traceparent` headers after a retry or DLQ re-drive, and
  `TraceContext.Extract` reads the first one. The reference compacts in place and keeps
  one header.
- **Extract onto the caller's ctx.** `prop.Extract(ctx, carrier)` keeps the poll loop's
  cancellation and deadlines. `prop.Extract(context.Background(), ...)` loses them.
- **Defaults.** `otel.GetTextMapPropagator()` is a no-op composite unless the app called
  `otel.SetTextMapPropagator`. A library that silently defaults to it produces exactly the
  "trace stops at Kafka" symptom. The reference defaults to TraceContext + Baggage.
- **Semconv.** `semconv.MessagingSystemKafka`, `MessagingDestinationName`,
  `MessagingDestinationPartitionID` (string!), `MessagingKafkaOffset`,
  `MessagingOperationTypeSend/Process`, `MessagingConsumerGroupName`, `ErrorType(err)`.
- **Child vs link.** One record, one process span: child gives a single trace in Tempo. For
  batches, start one `process` span per batch with `trace.WithLinks(...)` to every record's
  extracted span context; a single parent would be wrong there because the batch has many.

## Production notes a strong answer mentions

- franz-go ships `plugin/kotel`, which hooks produce/fetch automatically; the hand-rolled
  version is useful for understanding and for per-record `process` spans that kotel cannot
  know about.
- Sampling: parent-based sampling means the API's decision flows through Kafka; do tail
  sampling in the collector for error/latency-based retention.
- Baggage goes on the wire to every downstream service: no PII, keep it small.
- Span duration on the consumer is processing time; queue time is
  `consumer_span.start - producer_span.end`, and consumer lag belongs in metrics.
