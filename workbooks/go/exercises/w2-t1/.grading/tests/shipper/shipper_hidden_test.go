package shipper

import (
	"context"
	"errors"
	"fmt"
	"runtime"
	"slices"
	"sync"
	"testing"
	"time"
)

// settle waits until the goroutine count drops to at most want, or times out.
func settle(t *testing.T, want int, within time.Duration) int {
	t.Helper()
	deadline := time.Now().Add(within)
	n := runtime.NumGoroutine()
	for time.Now().Before(deadline) {
		runtime.GC()
		n = runtime.NumGoroutine()
		if n <= want {
			return n
		}
		time.Sleep(10 * time.Millisecond)
	}
	return n
}

func TestHiddenNoLeakWhenSinkIgnoresContext(t *testing.T) {
	base := runtime.NumGoroutine()
	s := New(slowSink{delay: 60 * time.Millisecond}, Config{SendTimeout: 5 * time.Millisecond, MaxRetries: -1})
	for i := 0; i < 50; i++ {
		_ = s.Flush(context.Background(), []string{"line"})
	}
	// Every sink call returns after 60ms; nothing should still be parked after that.
	if n := settle(t, base+2, 2*time.Second); n > base+2 {
		t.Fatalf("goroutines did not return to baseline: base=%d now=%d (leaked senders?)", base, n)
	}
}

func TestHiddenNoLeakWhenSinkHonoursContext(t *testing.T) {
	base := runtime.NumGoroutine()
	s := New(ctxSink{delay: time.Hour}, Config{SendTimeout: 5 * time.Millisecond, MaxRetries: 1, Backoff: time.Millisecond})
	for i := 0; i < 50; i++ {
		if err := s.Flush(context.Background(), []string{"line"}); !errors.Is(err, context.DeadlineExceeded) {
			t.Fatalf("want DeadlineExceeded, got %v", err)
		}
	}
	if n := settle(t, base+2, 2*time.Second); n > base+2 {
		t.Fatalf("goroutines did not return to baseline: base=%d now=%d", base, n)
	}
}

func TestHiddenNoLeakOnParentCancel(t *testing.T) {
	base := runtime.NumGoroutine()
	s := New(ctxSink{delay: time.Hour}, Config{SendTimeout: time.Second, MaxRetries: 3, Backoff: time.Millisecond})
	var wg sync.WaitGroup
	for i := 0; i < 20; i++ {
		ctx, cancel := context.WithCancel(context.Background())
		wg.Add(1)
		go func() {
			defer wg.Done()
			_ = s.Flush(ctx, []string{"line"})
		}()
		time.AfterFunc(5*time.Millisecond, cancel)
	}
	wg.Wait()
	if n := settle(t, base+2, 2*time.Second); n > base+2 {
		t.Fatalf("goroutines did not return to baseline after cancel: base=%d now=%d", base, n)
	}
}

func TestHiddenRetriesThenDelivers(t *testing.T) {
	sink := &recordingSink{failN: 2, failErr: errors.New("503 from bulk endpoint")}
	s := New(sink, Config{SendTimeout: time.Second, MaxRetries: 3, Backoff: time.Millisecond})
	if err := s.Flush(context.Background(), []string{"a", "b"}); err != nil {
		t.Fatalf("Flush: %v", err)
	}
	if sink.calls != 3 {
		t.Fatalf("sink called %d times, want 3", sink.calls)
	}
	if s.Stats.Attempts.Load() != 3 || s.Stats.BatchesSent.Load() != 1 {
		t.Fatalf("stats: attempts=%d sent=%d", s.Stats.Attempts.Load(), s.Stats.BatchesSent.Load())
	}
	if !slices.Equal(sink.lines(), []string{"a", "b"}) {
		t.Fatalf("lines = %v", sink.lines())
	}
}

func TestHiddenAllAttemptsFailWrapsLastError(t *testing.T) {
	boom := errors.New("403 forbidden")
	sink := &recordingSink{failN: 100, failErr: boom}
	s := New(sink, Config{SendTimeout: time.Second, MaxRetries: 2, Backoff: time.Millisecond})
	err := s.Flush(context.Background(), []string{"a"})
	if !errors.Is(err, boom) {
		t.Fatalf("want error wrapping the sink error, got %v", err)
	}
	if sink.calls != 3 || s.Stats.BatchesFailed.Load() != 1 {
		t.Fatalf("calls=%d failed=%d", sink.calls, s.Stats.BatchesFailed.Load())
	}
}

func TestHiddenTimeoutBoundsEachAttempt(t *testing.T) {
	s := New(slowSink{delay: 500 * time.Millisecond}, Config{SendTimeout: 20 * time.Millisecond, MaxRetries: 2, Backoff: time.Millisecond})
	start := time.Now()
	err := s.Flush(context.Background(), []string{"a"})
	if !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("want DeadlineExceeded, got %v", err)
	}
	if el := time.Since(start); el > 300*time.Millisecond {
		t.Fatalf("3 attempts at 20ms took %v; each attempt must be bounded by SendTimeout", el)
	}
	if s.Stats.Timeouts.Load() != 3 {
		t.Fatalf("Timeouts = %d, want 3", s.Stats.Timeouts.Load())
	}
}

func TestHiddenConcurrentFlushRaceFree(t *testing.T) {
	sink := &recordingSink{}
	s := New(sink, Config{SendTimeout: time.Second})
	var wg sync.WaitGroup
	for i := 0; i < 32; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if err := s.Flush(context.Background(), []string{fmt.Sprintf("line-%d", i)}); err != nil {
				t.Errorf("Flush: %v", err)
			}
		}()
	}
	wg.Wait()
	if got := len(sink.lines()); got != 32 {
		t.Fatalf("delivered %d lines, want 32", got)
	}
}

func TestHiddenSteadyStateUnderSustainedTimeouts(t *testing.T) {
	// Production shape: 8 tailers, bulk endpoint stuck for a while, sink ignores ctx.
	base := runtime.NumGoroutine()
	s := New(slowSink{delay: 30 * time.Millisecond}, Config{SendTimeout: 2 * time.Millisecond, MaxRetries: 1, Backoff: time.Millisecond})
	var wg sync.WaitGroup
	for w := 0; w < 8; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for i := 0; i < 25; i++ {
				_ = s.Flush(context.Background(), []string{"x"})
			}
		}()
	}
	wg.Wait()
	if n := settle(t, base+2, 2*time.Second); n > base+2 {
		t.Fatalf("goroutines grew from %d to %d", base, n)
	}
}
