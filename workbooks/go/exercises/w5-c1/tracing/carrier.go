// Package tracing propagates OpenTelemetry trace context across Kafka using
// franz-go record headers. See README.md for the requirements.
package tracing

import (
	"github.com/twmb/franz-go/pkg/kgo"
	"go.opentelemetry.io/otel/propagation"
)

// HeaderCarrier adapts the headers of a single *kgo.Record to
// propagation.TextMapCarrier so a TextMapPropagator can Inject/Extract.
type HeaderCarrier struct {
	R *kgo.Record
}

var _ propagation.TextMapCarrier = HeaderCarrier{}

// Get returns the value of the first header with exactly this key, or "".
func (c HeaderCarrier) Get(key string) string {
	// TODO
	return ""
}

// Set stores key=value. If a header with this key already exists it is
// replaced in place (Kafka allows duplicate header keys; we must not create them).
func (c HeaderCarrier) Set(key, value string) {
	// TODO
}

// Keys returns every header key, in header order.
func (c HeaderCarrier) Keys() []string {
	// TODO
	return nil
}
