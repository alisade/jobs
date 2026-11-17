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
	if c.R == nil {
		return ""
	}
	for _, h := range c.R.Headers {
		if h.Key == key {
			return string(h.Value)
		}
	}
	return ""
}

// Set stores key=value, replacing an existing header with the same key and
// dropping any later duplicates of it.
func (c HeaderCarrier) Set(key, value string) {
	if c.R == nil {
		return
	}
	out := c.R.Headers[:0]
	replaced := false
	for _, h := range c.R.Headers {
		if h.Key == key {
			if replaced {
				continue
			}
			h.Value = []byte(value)
			replaced = true
		}
		out = append(out, h)
	}
	if !replaced {
		out = append(out, kgo.RecordHeader{Key: key, Value: []byte(value)})
	}
	c.R.Headers = out
}

// Keys returns every header key, in header order.
func (c HeaderCarrier) Keys() []string {
	if c.R == nil {
		return nil
	}
	keys := make([]string, 0, len(c.R.Headers))
	for _, h := range c.R.Headers {
		keys = append(keys, h.Key)
	}
	return keys
}
