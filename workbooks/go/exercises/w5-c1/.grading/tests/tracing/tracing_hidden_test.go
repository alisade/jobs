package tracing

import (
	"context"
	"errors"
	"strconv"
	"strings"
	"testing"

	"github.com/twmb/franz-go/pkg/kgo"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/baggage"
	"go.opentelemetry.io/otel/codes"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	"go.opentelemetry.io/otel/trace"
)

func attrMap(s sdktrace.ReadOnlySpan) map[attribute.Key]attribute.Value {
	m := map[attribute.Key]attribute.Value{}
	for _, kv := range s.Attributes() {
		m[kv.Key] = kv.Value
	}
	return m
}

func headerCount(r *kgo.Record, key string) int {
	n := 0
	for _, h := range r.Headers {
		if h.Key == key {
			n++
		}
	}
	return n
}

// produceAndConsume runs one record through Producer and Consumer and returns the
// producer span, consumer span and the ctx the handler saw.
func produceAndConsume(t *testing.T, prodCtx context.Context, cfg Config, group string) (sdktrace.ReadOnlySpan, sdktrace.ReadOnlySpan, context.Context, *kgo.Record) {
	t.Helper()
	cluster := newCluster(t)
	r := &kgo.Record{Topic: testTopic, Key: []byte("tenant-7"), Value: []byte("x")}
	if err := NewProducer(newClient(t, cluster), cfg).ProduceSync(prodCtx, r); err != nil {
		t.Fatalf("ProduceSync: %v", err)
	}
	got := consumeN(t, cluster, 1)[0]
	var hctx context.Context
	if err := NewConsumer(group, cfg).Process(context.Background(), got, func(ctx context.Context, _ *kgo.Record) error {
		hctx = ctx
		return nil
	}); err != nil {
		t.Fatalf("Process: %v", err)
	}
	return nil, nil, hctx, got
}

func onlySpan(t *testing.T, spans []sdktrace.ReadOnlySpan, what string) sdktrace.ReadOnlySpan {
	t.Helper()
	if len(spans) != 1 {
		t.Fatalf("want exactly 1 %s span, got %d", what, len(spans))
	}
	return spans[0]
}

func TestHiddenConsumerSpanIsChildOfProducerSpan(t *testing.T) {
	tp, rec, prop := telemetry()
	_, _, hctx, _ := produceAndConsume(t, context.Background(), Config{TracerProvider: tp, Propagator: prop}, "task-runner")
	prod := onlySpan(t, spansByKind(rec, trace.SpanKindProducer), "PRODUCER")
	cons := onlySpan(t, spansByKind(rec, trace.SpanKindConsumer), "CONSUMER")
	if cons.Parent().SpanID() != prod.SpanContext().SpanID() {
		t.Fatalf("consumer parent span id = %s, want producer span id %s", cons.Parent().SpanID(), prod.SpanContext().SpanID())
	}
	if !cons.Parent().IsRemote() {
		t.Fatal("consumer parent should be a remote span context extracted from headers")
	}
	if got := trace.SpanContextFromContext(hctx); got.SpanID() != cons.SpanContext().SpanID() {
		t.Fatal("handler ctx must carry the CONSUMER span so downstream calls nest under it")
	}
}

func TestHiddenProducerSpanParentsOnCallerContext(t *testing.T) {
	tp, rec, prop := telemetry()
	ctx, parent := tp.Tracer("api").Start(context.Background(), "POST /tasks")
	produceAndConsume(t, ctx, Config{TracerProvider: tp, Propagator: prop}, "task-runner")
	parent.End()
	prod := onlySpan(t, spansByKind(rec, trace.SpanKindProducer), "PRODUCER")
	if prod.Parent().SpanID() != parent.SpanContext().SpanID() {
		t.Fatal("PRODUCER span must be a child of the span in the caller's ctx")
	}
	cons := onlySpan(t, spansByKind(rec, trace.SpanKindConsumer), "CONSUMER")
	if cons.SpanContext().TraceID() != parent.SpanContext().TraceID() {
		t.Fatal("HTTP request, produce and process must share one trace")
	}
}

func TestHiddenSpanNamesAndKindsFollowSemconv(t *testing.T) {
	tp, rec, prop := telemetry()
	produceAndConsume(t, context.Background(), Config{TracerProvider: tp, Propagator: prop}, "task-runner")
	prod := onlySpan(t, spansByKind(rec, trace.SpanKindProducer), "PRODUCER")
	cons := onlySpan(t, spansByKind(rec, trace.SpanKindConsumer), "CONSUMER")
	if prod.Name() != "send "+testTopic {
		t.Fatalf("producer span name = %q, want %q", prod.Name(), "send "+testTopic)
	}
	if cons.Name() != "process "+testTopic {
		t.Fatalf("consumer span name = %q, want %q", cons.Name(), "process "+testTopic)
	}
	if prod.InstrumentationScope().Name != ScopeName || cons.InstrumentationScope().Name != ScopeName {
		t.Fatalf("tracer scope name must be ScopeName, got %q / %q", prod.InstrumentationScope().Name, cons.InstrumentationScope().Name)
	}
}

func TestHiddenMessagingAttributes(t *testing.T) {
	tp, rec, prop := telemetry()
	_, _, _, got := produceAndConsume(t, context.Background(), Config{TracerProvider: tp, Propagator: prop}, "task-runner")
	prod := attrMap(onlySpan(t, spansByKind(rec, trace.SpanKindProducer), "PRODUCER"))
	cons := attrMap(onlySpan(t, spansByKind(rec, trace.SpanKindConsumer), "CONSUMER"))

	for name, m := range map[string]map[attribute.Key]attribute.Value{"producer": prod, "consumer": cons} {
		if m["messaging.system"].AsString() != "kafka" {
			t.Errorf("%s: messaging.system = %q, want kafka", name, m["messaging.system"].AsString())
		}
		if m["messaging.destination.name"].AsString() != testTopic {
			t.Errorf("%s: messaging.destination.name = %q", name, m["messaging.destination.name"].AsString())
		}
		if m["messaging.destination.partition.id"].AsString() != strconv.Itoa(int(got.Partition)) {
			t.Errorf("%s: messaging.destination.partition.id = %q, want %d", name, m["messaging.destination.partition.id"].AsString(), got.Partition)
		}
		if v, ok := m["messaging.kafka.offset"]; !ok || v.AsInt64() != got.Offset {
			t.Errorf("%s: messaging.kafka.offset = %v, want %d", name, v.Emit(), got.Offset)
		}
	}
	if prod["messaging.operation.type"].AsString() != "send" {
		t.Errorf("producer messaging.operation.type = %q, want send", prod["messaging.operation.type"].AsString())
	}
	if cons["messaging.operation.type"].AsString() != "process" {
		t.Errorf("consumer messaging.operation.type = %q, want process", cons["messaging.operation.type"].AsString())
	}
	if cons["messaging.consumer.group.name"].AsString() != "task-runner" {
		t.Errorf("consumer messaging.consumer.group.name = %q, want task-runner", cons["messaging.consumer.group.name"].AsString())
	}
}

func TestHiddenBaggagePropagates(t *testing.T) {
	tp, _, prop := telemetry()
	m, _ := baggage.NewMember("tenant.id", "acme-7")
	b, _ := baggage.New(m)
	ctx := baggage.ContextWithBaggage(context.Background(), b)
	_, _, hctx, got := produceAndConsume(t, ctx, Config{TracerProvider: tp, Propagator: prop}, "g")
	if headerCount(got, "baggage") != 1 {
		t.Fatalf("want one baggage header on the record, headers=%v", got.Headers)
	}
	if v := baggage.FromContext(hctx).Member("tenant.id").Value(); v != "acme-7" {
		t.Fatalf("handler ctx baggage tenant.id = %q, want acme-7", v)
	}
}

func TestHiddenReproduceDoesNotDuplicateHeaders(t *testing.T) {
	cluster := newCluster(t)
	tp, rec, prop := telemetry()
	p := NewProducer(newClient(t, cluster), Config{TracerProvider: tp, Propagator: prop})
	r := &kgo.Record{Topic: testTopic, Value: []byte("retry-me"), Headers: []kgo.RecordHeader{{Key: "x-attempt", Value: []byte("1")}}}
	for i := 0; i < 2; i++ {
		if err := p.ProduceSync(context.Background(), r); err != nil {
			t.Fatalf("ProduceSync #%d: %v", i, err)
		}
	}
	if n := headerCount(r, "traceparent"); n != 1 {
		t.Fatalf("after re-producing the same record there are %d traceparent headers, want 1", n)
	}
	if n := headerCount(r, "x-attempt"); n != 1 {
		t.Fatal("unrelated headers must be preserved")
	}
	prods := spansByKind(rec, trace.SpanKindProducer)
	if len(prods) != 2 {
		t.Fatalf("want 2 producer spans, got %d", len(prods))
	}
	tpHeader := HeaderCarrier{R: r}.Get("traceparent")
	if !strings.Contains(tpHeader, prods[1].SpanContext().SpanID().String()) {
		t.Fatalf("traceparent %q must reference the latest producer span %s", tpHeader, prods[1].SpanContext().SpanID())
	}
}

func TestHiddenCarrierSetCollapsesExistingDuplicates(t *testing.T) {
	r := &kgo.Record{Headers: []kgo.RecordHeader{
		{Key: "traceparent", Value: []byte("old-1")},
		{Key: "a", Value: []byte("1")},
		{Key: "traceparent", Value: []byte("old-2")},
	}}
	HeaderCarrier{R: r}.Set("traceparent", "new")
	c := HeaderCarrier{R: r}
	if headerCount(r, "traceparent") != 1 || c.Get("traceparent") != "new" {
		t.Fatalf("Set must leave exactly one header with the new value, got %v", r.Headers)
	}
	if c.Get("missing") != "" {
		t.Fatal("Get on a missing key must return empty string")
	}
	if c.Get("TRACEPARENT") != "" {
		t.Fatal("Kafka header keys are case-sensitive; do not fold case")
	}
}

func TestHiddenConsumerHandlerErrorSetsStatus(t *testing.T) {
	tp, rec, prop := telemetry()
	cfg := Config{TracerProvider: tp, Propagator: prop}
	r := &kgo.Record{Topic: testTopic, Partition: 2, Offset: 41}
	boom := errors.New("tool call failed: upstream 503")
	err := NewConsumer("g", cfg).Process(context.Background(), r, func(context.Context, *kgo.Record) error { return boom })
	if !errors.Is(err, boom) {
		t.Fatalf("Process must return the handler error, got %v", err)
	}
	cons := onlySpan(t, spansByKind(rec, trace.SpanKindConsumer), "CONSUMER")
	if cons.Status().Code != codes.Error {
		t.Fatalf("span status = %v, want Error", cons.Status().Code)
	}
	found := false
	for _, ev := range cons.Events() {
		if ev.Name == "exception" {
			found = true
		}
	}
	if !found {
		t.Fatal("handler error must be recorded on the span (span.RecordError)")
	}
	if _, ok := attrMap(cons)["error.type"]; !ok {
		t.Fatal("failed span should carry error.type (semconv)")
	}
}

func TestHiddenProducerErrorSetsStatus(t *testing.T) {
	cluster := newCluster(t)
	tp, rec, prop := telemetry()
	p := NewProducer(newClient(t, cluster), Config{TracerProvider: tp, Propagator: prop})
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	err := p.ProduceSync(ctx, &kgo.Record{Topic: testTopic, Value: []byte("x")})
	if err == nil {
		t.Fatal("ProduceSync with a cancelled ctx must return an error")
	}
	prod := onlySpan(t, spansByKind(rec, trace.SpanKindProducer), "PRODUCER")
	if prod.Status().Code != codes.Error {
		t.Fatalf("producer span status = %v, want Error", prod.Status().Code)
	}
}

func TestHiddenSuccessfulSpansAreNotErrors(t *testing.T) {
	tp, rec, prop := telemetry()
	produceAndConsume(t, context.Background(), Config{TracerProvider: tp, Propagator: prop}, "g")
	for _, s := range rec.Ended() {
		if s.Status().Code == codes.Error {
			t.Fatalf("span %q has Error status on the happy path", s.Name())
		}
	}
	if len(rec.Ended()) != 2 {
		t.Fatalf("want exactly 2 ended spans (send + process), got %d", len(rec.Ended()))
	}
}

func TestHiddenNoTraceparentStartsNewRoot(t *testing.T) {
	tp, rec, prop := telemetry()
	r := &kgo.Record{Topic: testTopic, Value: []byte("legacy producer, no headers")}
	var hctx context.Context
	if err := NewConsumer("g", Config{TracerProvider: tp, Propagator: prop}).Process(context.Background(), r, func(ctx context.Context, _ *kgo.Record) error {
		hctx = ctx
		return nil
	}); err != nil {
		t.Fatalf("Process: %v", err)
	}
	cons := onlySpan(t, spansByKind(rec, trace.SpanKindConsumer), "CONSUMER")
	if cons.Parent().IsValid() {
		t.Fatal("with no traceparent header the consumer span must be a root")
	}
	if !trace.SpanContextFromContext(hctx).IsValid() {
		t.Fatal("handler ctx must still carry a valid span")
	}
}

func TestHiddenHandlerCtxKeepsCallerCancellation(t *testing.T) {
	tp, _, prop := telemetry()
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	r := &kgo.Record{Topic: testTopic}
	var seen error
	_ = NewConsumer("g", Config{TracerProvider: tp, Propagator: prop}).Process(ctx, r, func(hctx context.Context, _ *kgo.Record) error {
		seen = hctx.Err()
		return nil
	})
	if !errors.Is(seen, context.Canceled) {
		t.Fatal("extract onto the caller's ctx: the handler must observe shutdown cancellation")
	}
}

func TestHiddenNilPropagatorDefaultsToW3CNotGlobal(t *testing.T) {
	// The global propagator is a no-op by default; relying on it silently drops headers.
	tp, rec, _ := telemetry()
	_, _, hctx, got := produceAndConsume(t, context.Background(), Config{TracerProvider: tp}, "g")
	if headerCount(got, "traceparent") != 1 {
		t.Fatalf("with Config.Propagator nil, traceparent must still be injected; headers=%v", got.Headers)
	}
	prod := onlySpan(t, spansByKind(rec, trace.SpanKindProducer), "PRODUCER")
	if trace.SpanContextFromContext(hctx).TraceID() != prod.SpanContext().TraceID() {
		t.Fatal("default propagator must also extract on the consumer side")
	}
}

func TestHiddenNoGlobalProviderMutation(t *testing.T) {
	before := otel.GetTracerProvider()
	tp, _, prop := telemetry()
	produceAndConsume(t, context.Background(), Config{TracerProvider: tp, Propagator: prop}, "g")
	if otel.GetTracerProvider() != before {
		t.Fatal("package must not call otel.SetTracerProvider; providers are injected")
	}
}
