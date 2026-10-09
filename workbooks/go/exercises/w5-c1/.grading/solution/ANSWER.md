# go/w5-c1 ANSWER (model)

## Approach

Wrote the carrier first with table tests for duplicates and case sensitivity, then the
producer and consumer against kfake with a SpanRecorder. Chose child spans: one record per
process span and on-call wants a single trace from HTTP request to tool call.

## Fix

- `HeaderCarrier.Set` compacts the header slice in place and keeps exactly one entry per key.
- `ProduceSync`: start PRODUCER span `send <topic>`, inject from the span ctx, `ProduceSync`,
  set partition/offset on success, record error + status + `error.type` on failure.
- `Process`: extract onto the caller ctx, CONSUMER span `process <topic>` as child, handler
  gets the span ctx and baggage, errors recorded and returned unchanged.
- Nil propagator defaults to TraceContext + Baggage; nothing calls `otel.Set*`.

## Trade-offs / what I would do in production

- Batch handlers: one span per batch with links to each record's context.
- Consider `kotel` for client-level produce/fetch spans and keep this for process spans.
- Tail sampling in the collector; keep baggage small and free of PII.
- Alert on consumer lag from metrics, not span latency.
