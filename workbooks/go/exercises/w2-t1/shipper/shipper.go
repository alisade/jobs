// Package shipper batches log lines, gzips them and sends them to a Sink
// (the OpenSearch bulk endpoint in production). It is the core of driftwood,
// Tidewater Analytics' node-level log shipper (one DaemonSet pod per node).
package shipper

import (
	"bytes"
	"compress/gzip"
	"context"
	"errors"
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

// Sink delivers one gzipped batch. The production sink wraps a vendor SDK
// whose client does NOT reliably honour ctx (it has its own internal retry
// and socket timeouts), which is why Shipper enforces SendTimeout itself.
type Sink interface {
	Send(ctx context.Context, payload []byte) error
}

// Config controls batching and delivery.
type Config struct {
	SendTimeout time.Duration // per attempt; default 5s
	MaxRetries  int           // extra attempts after the first; default 3
	Backoff     time.Duration // base backoff between attempts, doubled each retry; default 200ms
}

// Stats are exported as Prometheus counters by cmd/driftwood.
type Stats struct {
	BatchesSent   atomic.Int64
	BatchesFailed atomic.Int64
	Attempts      atomic.Int64
	Timeouts      atomic.Int64
}

// Shipper is safe for concurrent use; driftwood runs one Flush per tailed file.
type Shipper struct {
	sink  Sink
	cfg   Config
	Stats Stats

	// bufPool recycles compression buffers. Batches are capped at 1 MiB of
	// input by the tailer, so pooled buffers are bounded in size.
	bufPool sync.Pool
}

// New returns a Shipper with defaults applied.
func New(sink Sink, cfg Config) *Shipper {
	if cfg.SendTimeout <= 0 {
		cfg.SendTimeout = 5 * time.Second
	}
	if cfg.MaxRetries < 0 {
		cfg.MaxRetries = 0
	} else if cfg.MaxRetries == 0 {
		cfg.MaxRetries = 3
	}
	if cfg.Backoff <= 0 {
		cfg.Backoff = 200 * time.Millisecond
	}
	s := &Shipper{sink: sink, cfg: cfg}
	s.bufPool.New = func() any { return new(bytes.Buffer) }
	return s
}

// Flush compresses lines into one batch and delivers it, retrying with
// exponential backoff. It returns when the batch is delivered, when all
// attempts failed, or when ctx is done.
func (s *Shipper) Flush(ctx context.Context, lines []string) error {
	if len(lines) == 0 {
		return nil
	}
	payload, err := s.compress(lines)
	if err != nil {
		return fmt.Errorf("shipper: compress: %w", err)
	}

	var lastErr error
	backoff := s.cfg.Backoff
	for attempt := 0; attempt <= s.cfg.MaxRetries; attempt++ {
		if attempt > 0 {
			t := time.NewTimer(backoff)
			select {
			case <-ctx.Done():
				t.Stop()
				s.Stats.BatchesFailed.Add(1)
				return fmt.Errorf("shipper: giving up after %d attempts: %w", attempt, ctx.Err())
			case <-t.C:
			}
			backoff *= 2
		}
		lastErr = s.sendOnce(ctx, payload)
		if lastErr == nil {
			s.Stats.BatchesSent.Add(1)
			return nil
		}
		if ctx.Err() != nil {
			break
		}
	}
	s.Stats.BatchesFailed.Add(1)
	return fmt.Errorf("shipper: batch not delivered: %w", lastErr)
}

// sendOnce makes one delivery attempt bounded by SendTimeout, even when the
// sink ignores ctx.
func (s *Shipper) sendOnce(ctx context.Context, payload []byte) error {
	s.Stats.Attempts.Add(1)
	ctx, cancel := context.WithTimeout(ctx, s.cfg.SendTimeout)
	defer cancel()

	result := make(chan error)
	go func() {
		result <- s.sink.Send(ctx, payload)
	}()

	select {
	case err := <-result:
		return err
	case <-ctx.Done():
		if errors.Is(ctx.Err(), context.DeadlineExceeded) {
			s.Stats.Timeouts.Add(1)
		}
		return ctx.Err()
	}
}

// compress gzips lines (newline-delimited) into a fresh payload slice. The
// scratch buffer goes back to the pool; the returned slice is owned by the
// caller.
func (s *Shipper) compress(lines []string) ([]byte, error) {
	buf := s.bufPool.Get().(*bytes.Buffer)
	buf.Reset()
	defer s.bufPool.Put(buf)

	zw := gzip.NewWriter(buf)
	for _, l := range lines {
		if _, err := zw.Write([]byte(l)); err != nil {
			return nil, err
		}
		if _, err := zw.Write([]byte{'\n'}); err != nil {
			return nil, err
		}
	}
	if err := zw.Close(); err != nil {
		return nil, err
	}
	return bytes.Clone(buf.Bytes()), nil
}
