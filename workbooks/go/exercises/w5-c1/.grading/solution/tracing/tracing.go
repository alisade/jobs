package tracing

import (
	"context"
	"strconv"

	"github.com/twmb/franz-go/pkg/kgo"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/codes"
	"go.opentelemetry.io/otel/propagation"
	semconv "go.opentelemetry.io/otel/semconv/v1.43.0"
	"go.opentelemetry.io/otel/trace"
)

// ScopeName is the instrumentation scope used for every span this package creates.
const ScopeName = "github.com/relaypoint/taskbus/tracing"

// Config injects telemetry dependencies.
type Config struct {
	TracerProvider trace.TracerProvider
	Propagator     propagation.TextMapPropagator
}

func (cfg Config) tracer() trace.Tracer {
	tp := cfg.TracerProvider
	if tp == nil {
		tp = otel.GetTracerProvider()
	}
	return tp.Tracer(ScopeName)
}

func (cfg Config) propagator() propagation.TextMapPropagator {
	if cfg.Propagator != nil {
		return cfg.Propagator
	}
	return propagation.NewCompositeTextMapPropagator(propagation.TraceContext{}, propagation.Baggage{})
}

// Handler processes one record.
type Handler func(ctx context.Context, r *kgo.Record) error

// Producer wraps a *kgo.Client and traces every produce.
type Producer struct {
	client *kgo.Client
	tracer trace.Tracer
	prop   propagation.TextMapPropagator
}

// NewProducer builds a traced producer.
func NewProducer(client *kgo.Client, cfg Config) *Producer {
	return &Producer{client: client, tracer: cfg.tracer(), prop: cfg.propagator()}
}

// ProduceSync produces r inside a PRODUCER span and injects its context.
func (p *Producer) ProduceSync(ctx context.Context, r *kgo.Record) error {
	ctx, span := p.tracer.Start(ctx, "send "+r.Topic,
		trace.WithSpanKind(trace.SpanKindProducer),
		trace.WithAttributes(
			semconv.MessagingSystemKafka,
			semconv.MessagingDestinationName(r.Topic),
			semconv.MessagingOperationTypeSend,
			semconv.MessagingOperationName("send"),
		))
	defer span.End()

	// Inject AFTER starting the span so the header names this span as parent.
	// Set replaces, so re-producing the same record does not duplicate headers.
	p.prop.Inject(ctx, HeaderCarrier{R: r})

	err := p.client.ProduceSync(ctx, r).FirstErr()
	if err != nil {
		span.RecordError(err)
		span.SetStatus(codes.Error, err.Error())
		span.SetAttributes(semconv.ErrorType(err))
		return err
	}
	span.SetAttributes(
		semconv.MessagingDestinationPartitionID(strconv.Itoa(int(r.Partition))),
		semconv.MessagingKafkaOffset(int(r.Offset)),
	)
	return nil
}

// Consumer traces the processing of consumed records.
type Consumer struct {
	group  string
	tracer trace.Tracer
	prop   propagation.TextMapPropagator
}

// NewConsumer builds a traced consumer for the given consumer group name.
func NewConsumer(group string, cfg Config) *Consumer {
	return &Consumer{group: group, tracer: cfg.tracer(), prop: cfg.propagator()}
}

// Process runs h inside a CONSUMER span that is a child of the producer span.
func (c *Consumer) Process(ctx context.Context, r *kgo.Record, h Handler) error {
	// Extract onto the caller's ctx so cancellation/deadlines survive.
	ctx = c.prop.Extract(ctx, HeaderCarrier{R: r})
	attrs := []attribute.KeyValue{
		semconv.MessagingSystemKafka,
		semconv.MessagingDestinationName(r.Topic),
		semconv.MessagingOperationTypeProcess,
		semconv.MessagingOperationName("process"),
		semconv.MessagingDestinationPartitionID(strconv.Itoa(int(r.Partition))),
		semconv.MessagingKafkaOffset(int(r.Offset)),
	}
	if c.group != "" {
		attrs = append(attrs, semconv.MessagingConsumerGroupName(c.group))
	}
	ctx, span := c.tracer.Start(ctx, "process "+r.Topic,
		trace.WithSpanKind(trace.SpanKindConsumer),
		trace.WithAttributes(attrs...))
	defer span.End()

	if err := h(ctx, r); err != nil {
		span.RecordError(err)
		span.SetStatus(codes.Error, err.Error())
		span.SetAttributes(semconv.ErrorType(err))
		return err
	}
	return nil
}
