package tracing

import (
	"context"
	"testing"
	"time"

	"github.com/twmb/franz-go/pkg/kfake"
	"github.com/twmb/franz-go/pkg/kgo"
	"go.opentelemetry.io/otel/propagation"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	"go.opentelemetry.io/otel/sdk/trace/tracetest"
	"go.opentelemetry.io/otel/trace"
)

const testTopic = "agent.tasks"

// newCluster starts an in-process fake Kafka cluster (no Docker needed).
func newCluster(t *testing.T) *kfake.Cluster {
	t.Helper()
	c, err := kfake.NewCluster(kfake.NumBrokers(1), kfake.SeedTopics(3, testTopic))
	if err != nil {
		t.Fatalf("kfake: %v", err)
	}
	t.Cleanup(c.Close)
	return c
}

func newClient(t *testing.T, c *kfake.Cluster, opts ...kgo.Opt) *kgo.Client {
	t.Helper()
	opts = append([]kgo.Opt{kgo.SeedBrokers(c.ListenAddrs()...)}, opts...)
	cl, err := kgo.NewClient(opts...)
	if err != nil {
		t.Fatalf("kgo.NewClient: %v", err)
	}
	t.Cleanup(cl.Close)
	return cl
}

// consumeN reads n records from testTopic from the start (direct partition
// consumer, no group join so tests stay fast).
func consumeN(t *testing.T, c *kfake.Cluster, n int) []*kgo.Record {
	t.Helper()
	cl := newClient(t, c, kgo.ConsumeTopics(testTopic), kgo.ConsumeResetOffset(kgo.NewOffset().AtStart()))
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	var out []*kgo.Record
	for len(out) < n {
		fs := cl.PollFetches(ctx)
		if ctx.Err() != nil {
			t.Fatalf("timed out after consuming %d/%d records", len(out), n)
		}
		fs.EachRecord(func(r *kgo.Record) { out = append(out, r) })
	}
	return out
}

// telemetry returns an isolated provider + recorder and the W3C propagator.
// Nothing touches the OTel globals.
func telemetry() (*sdktrace.TracerProvider, *tracetest.SpanRecorder, propagation.TextMapPropagator) {
	rec := tracetest.NewSpanRecorder()
	tp := sdktrace.NewTracerProvider(sdktrace.WithSpanProcessor(rec))
	prop := propagation.NewCompositeTextMapPropagator(propagation.TraceContext{}, propagation.Baggage{})
	return tp, rec, prop
}

func spansByKind(rec *tracetest.SpanRecorder, kind trace.SpanKind) []sdktrace.ReadOnlySpan {
	var out []sdktrace.ReadOnlySpan
	for _, s := range rec.Ended() {
		if s.SpanKind() == kind {
			out = append(out, s)
		}
	}
	return out
}
