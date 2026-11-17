package tracing

import (
	"context"
	"errors"

	"github.com/twmb/franz-go/pkg/kgo"
	"go.opentelemetry.io/otel/propagation"
	"go.opentelemetry.io/otel/trace"
)

// ScopeName is the instrumentation scope used for every span this package creates.
const ScopeName = "github.com/relaypoint/taskbus/tracing"

// Config injects telemetry dependencies. Nothing in this package may read or
// mutate the OTel globals except as the documented fallback below.
type Config struct {
	// TracerProvider used to create spans. Nil means otel.GetTracerProvider().
	TracerProvider trace.TracerProvider
	// Propagator used to inject/extract headers. Nil means a composite of
	// W3C TraceContext and W3C Baggage (NOT the global, which defaults to a no-op).
	Propagator propagation.TextMapPropagator
}

// Handler processes one record. ctx carries the CONSUMER span and any baggage
// the producer sent.
type Handler func(ctx context.Context, r *kgo.Record) error

// Producer wraps a *kgo.Client and traces every produce.
type Producer struct {
	client *kgo.Client
	// TODO: add tracer and propagator fields
}

// NewProducer builds a traced producer. See README.md requirement 2.
func NewProducer(client *kgo.Client, cfg Config) *Producer {
	// TODO
	return &Producer{client: client}
}

// ProduceSync starts a PRODUCER span named "send <topic>", injects the span
// context and baggage into r's headers, produces r synchronously, records the
// partition and offset, and ends the span. It returns the produce error.
func (p *Producer) ProduceSync(ctx context.Context, r *kgo.Record) error {
	// TODO
	return errors.New("not implemented")
}

// Consumer traces the processing of consumed records.
type Consumer struct {
	group string
	// TODO: add tracer and propagator fields
}

// NewConsumer builds a traced consumer for the given consumer group name.
func NewConsumer(group string, cfg Config) *Consumer {
	// TODO
	return &Consumer{group: group}
}

// Process extracts the producer's context from r's headers, starts a CONSUMER
// span named "process <topic>" as its child, calls h with a context carrying
// that span (and the baggage), records any error, and ends the span.
// It returns h's error unchanged.
func (c *Consumer) Process(ctx context.Context, r *kgo.Record, h Handler) error {
	// TODO
	return errors.New("not implemented")
}
