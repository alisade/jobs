# go/w5-c1 Trace agent tasks across Kafka with OpenTelemetry and franz-go

**Type:** coding | **Estimate:** 2.5 hours | **Week 5:** Prometheus/OTel, Istio/Envoy, Kafka with franz-go (Tue OpenTelemetry in Go, Fri Kafka from Go)

## Scenario

RelayPoint runs an agent platform on EKS. The `task-api` accepts a request over HTTP and
publishes an `agent.tasks` event to Kafka; `task-runner` pods consume it and call tools.
In Tempo every trace stops at the Kafka hop: the HTTP span and the runner's spans show
up as two unrelated traces, so on-call cannot tell which request caused a slow tool call.
A previous attempt "fixed" it by appending a `traceparent` header on every produce, which
broke the DLQ re-publisher: re-driven records carried two `traceparent` headers and
consumers picked the stale one.

You own the small `tracing` package both services import.

## Task

1. `tracing/carrier.go`: implement `HeaderCarrier` (a `propagation.TextMapCarrier` over
   `kgo.Record` headers).
2. `tracing/tracing.go`: implement `NewProducer` / `ProduceSync` and `NewConsumer` /
   `Process`. Keep the exported names and signatures; the hidden tests use them.
3. Fill in `ANSWER.md`.

## Requirements

1. **Carrier.** `Get` returns the first header with exactly that key (Kafka header keys
   are case-sensitive). `Set` replaces an existing header in place and leaves exactly one
   header with that key; other headers are preserved. `Keys` lists header keys in order.
2. **Dependencies are injected.** Use `Config.TracerProvider` and `Config.Propagator`.
   A nil provider falls back to `otel.GetTracerProvider()`; a nil propagator falls back to
   W3C TraceContext + Baggage (the global propagator is a no-op unless someone set it,
   which is exactly how propagation silently breaks). Never call `otel.Set*`.
3. **Producer.** `ProduceSync` starts a `PRODUCER` span named `send <topic>` as a child of
   the caller's ctx, injects that span's context (and baggage) into the record headers,
   produces synchronously, and on success sets partition and offset. Re-producing the
   same `*kgo.Record` must leave a single `traceparent` that points at the newest span.
4. **Consumer.** `Process` extracts from the headers **onto the caller's ctx** (so
   shutdown cancellation still reaches the handler), starts a `CONSUMER` span named
   `process <topic>` and calls the handler with a ctx carrying that span and the baggage.
   With no `traceparent`, the span is a new root.
5. **Parent, not link.** The consumer span is a **child** of the producer span: this
   pipeline processes one record per span and on-call wants one trace end to end. (For
   batch processing you would start one span per batch and add **links** to each
   record's producer context; mention this in `ANSWER.md`.)
6. **Semantic conventions** (`go.opentelemetry.io/otel/semconv/v1.43.0` is available) on
   both spans: `messaging.system=kafka`, `messaging.destination.name`,
   `messaging.destination.partition.id` (string), `messaging.kafka.offset`,
   `messaging.operation.type` (`send` / `process`); the consumer also sets
   `messaging.consumer.group.name`. Spans use the tracer scope `ScopeName`.
7. **Errors.** A failed produce or a handler error: `RecordError`, status `Error`, an
   `error.type` attribute, and the original error returned unchanged. Successful spans do
   not have `Error` status.

## Acceptance criteria

- `make test` passes with `-race`; `go vet` is clean.
- Hidden tests (in-process Kafka via `kfake`, spans captured with `tracetest.SpanRecorder`)
  check parent/child ids, span names and kinds, attributes, baggage, header de-duplication,
  error status, root spans without headers, ctx cancellation and the no-globals rule.

## How to run

```
make setup     # go mod download + build (kfake runs Kafka in-process)
make test      # visible tests
```

## What to submit

Your edits to `tracing/*.go` and `ANSWER.md`, then `/grade go/w5-c1` from the workbooks root.

## Study-guide links

- OTel context propagation: https://opentelemetry.io/docs/concepts/context-propagation/
- OTel Go instrumentation (spans, propagation): https://opentelemetry.io/docs/languages/go/instrumentation/
- OTel messaging semantic conventions (Kafka): https://opentelemetry.io/docs/specs/semconv/messaging/kafka/
- franz-go (kgo, plugins incl. kotel): https://github.com/twmb/franz-go
