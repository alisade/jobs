package tracing

import (
	"context"
	"slices"
	"testing"

	"github.com/twmb/franz-go/pkg/kgo"
	"go.opentelemetry.io/otel/trace"
)

func TestCarrierSetGetKeys(t *testing.T) {
	r := &kgo.Record{Headers: []kgo.RecordHeader{{Key: "tenant", Value: []byte("acme")}}}
	c := HeaderCarrier{R: r}
	c.Set("traceparent", "00-aaaa-bbbb-01")
	if got := c.Get("traceparent"); got != "00-aaaa-bbbb-01" {
		t.Fatalf("Get(traceparent) = %q", got)
	}
	if got := c.Get("tenant"); got != "acme" {
		t.Fatalf("existing header lost: Get(tenant) = %q", got)
	}
	if got := c.Keys(); !slices.Equal(got, []string{"tenant", "traceparent"}) {
		t.Fatalf("Keys() = %v", got)
	}
}

// Visible end-to-end happy path: the consumer span joins the producer's trace.
func TestTraceFlowsProducerToConsumer(t *testing.T) {
	cluster := newCluster(t)
	tp, rec, prop := telemetry()
	cfg := Config{TracerProvider: tp, Propagator: prop}

	p := NewProducer(newClient(t, cluster), cfg)
	if err := p.ProduceSync(context.Background(), &kgo.Record{Topic: testTopic, Value: []byte(`{"task":"summarize"}`)}); err != nil {
		t.Fatalf("ProduceSync: %v", err)
	}
	recs := consumeN(t, cluster, 1)

	c := NewConsumer("task-runner", cfg)
	if err := c.Process(context.Background(), recs[0], func(ctx context.Context, r *kgo.Record) error { return nil }); err != nil {
		t.Fatalf("Process: %v", err)
	}

	prod := spansByKind(rec, trace.SpanKindProducer)
	cons := spansByKind(rec, trace.SpanKindConsumer)
	if len(prod) != 1 || len(cons) != 1 {
		t.Fatalf("want 1 PRODUCER and 1 CONSUMER span, got %d and %d", len(prod), len(cons))
	}
	if prod[0].SpanContext().TraceID() != cons[0].SpanContext().TraceID() {
		t.Fatal("consumer span is in a different trace than the producer span")
	}
}
