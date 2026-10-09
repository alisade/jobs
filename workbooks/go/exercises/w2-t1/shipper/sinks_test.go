package shipper

import (
	"bytes"
	"compress/gzip"
	"context"
	"io"
	"strings"
	"sync"
	"time"
)

// recordingSink stores every payload it accepts.
type recordingSink struct {
	mu       sync.Mutex
	payloads [][]byte
	calls    int
	failN    int   // fail the first failN calls with failErr
	failErr  error // error used for the first failN calls
}

func (r *recordingSink) Send(ctx context.Context, p []byte) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.calls++
	if r.calls <= r.failN {
		return r.failErr
	}
	r.payloads = append(r.payloads, bytes.Clone(p))
	return nil
}

func (r *recordingSink) lines() []string {
	r.mu.Lock()
	defer r.mu.Unlock()
	var out []string
	for _, p := range r.payloads {
		zr, err := gzip.NewReader(bytes.NewReader(p))
		if err != nil {
			panic(err)
		}
		b, _ := io.ReadAll(zr)
		out = append(out, strings.Split(strings.TrimSuffix(string(b), "\n"), "\n")...)
	}
	return out
}

// slowSink models the vendor SDK: it sleeps for delay and ignores ctx.
type slowSink struct{ delay time.Duration }

func (s slowSink) Send(ctx context.Context, p []byte) error {
	time.Sleep(s.delay)
	return nil
}

// ctxSink honours ctx: it blocks until ctx is done or delay passes.
type ctxSink struct{ delay time.Duration }

func (s ctxSink) Send(ctx context.Context, p []byte) error {
	select {
	case <-time.After(s.delay):
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}
