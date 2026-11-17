package shipper

import (
	"context"
	"errors"
	"slices"
	"testing"
	"time"
)

func TestFlushDeliversLines(t *testing.T) {
	sink := &recordingSink{}
	s := New(sink, Config{SendTimeout: time.Second})
	in := []string{`{"level":"info","msg":"pod started"}`, `{"level":"warn","msg":"slow disk"}`}
	if err := s.Flush(context.Background(), in); err != nil {
		t.Fatalf("Flush: %v", err)
	}
	if got := sink.lines(); !slices.Equal(got, in) {
		t.Fatalf("delivered %q, want %q", got, in)
	}
	if s.Stats.BatchesSent.Load() != 1 {
		t.Fatalf("BatchesSent = %d, want 1", s.Stats.BatchesSent.Load())
	}
}

func TestFlushTimesOutOnSlowSink(t *testing.T) {
	s := New(slowSink{delay: 300 * time.Millisecond}, Config{SendTimeout: 20 * time.Millisecond, MaxRetries: -1})
	start := time.Now()
	err := s.Flush(context.Background(), []string{"x"})
	if !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("want DeadlineExceeded, got %v", err)
	}
	if el := time.Since(start); el > 200*time.Millisecond {
		t.Fatalf("Flush took %v; SendTimeout must bound each attempt even when the sink ignores ctx", el)
	}
}
