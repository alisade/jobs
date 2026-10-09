// Command driftwood reads newline-delimited JSON logs on stdin (fed by the
// node-level tailer), batches them and ships them to the OpenSearch bulk
// endpoint. It serves /debug/pprof and /metrics on :6060.
package main

import (
	"bufio"
	"bytes"
	"context"
	"flag"
	"fmt"
	"log/slog"
	"net/http"
	_ "net/http/pprof"
	"os"
	"os/signal"
	"runtime"
	"syscall"
	"time"

	"github.com/tidewater/driftwood/shipper"
)

type httpSink struct {
	url    string
	client *http.Client
}

func (h httpSink) Send(ctx context.Context, payload []byte) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, h.url, bytes.NewReader(payload))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Encoding", "gzip")
	req.Header.Set("Content-Type", "application/x-ndjson")
	resp, err := h.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		return fmt.Errorf("bulk endpoint: %s", resp.Status)
	}
	return nil
}

func main() {
	url := flag.String("endpoint", "http://localhost:9200/_bulk", "bulk endpoint")
	batch := flag.Int("batch", 500, "lines per batch")
	flag.Parse()

	log := slog.New(slog.NewJSONHandler(os.Stderr, nil))
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, os.Interrupt)
	defer stop()

	s := shipper.New(httpSink{url: *url, client: &http.Client{Timeout: 30 * time.Second}}, shipper.Config{})

	http.HandleFunc("/metrics", func(w http.ResponseWriter, _ *http.Request) {
		fmt.Fprintf(w, "go_goroutines %d\n", runtime.NumGoroutine())
		fmt.Fprintf(w, "driftwood_batches_sent_total %d\n", s.Stats.BatchesSent.Load())
		fmt.Fprintf(w, "driftwood_batches_failed_total %d\n", s.Stats.BatchesFailed.Load())
		fmt.Fprintf(w, "driftwood_send_attempts_total %d\n", s.Stats.Attempts.Load())
		fmt.Fprintf(w, "driftwood_send_timeouts_total %d\n", s.Stats.Timeouts.Load())
	})
	go func() { _ = http.ListenAndServe(":6060", nil) }()

	sc := bufio.NewScanner(os.Stdin)
	var lines []string
	for sc.Scan() {
		lines = append(lines, sc.Text())
		if len(lines) >= *batch {
			if err := s.Flush(ctx, lines); err != nil {
				log.Error("flush failed", "err", err, "lines", len(lines))
			}
			lines = nil
		}
	}
	if len(lines) > 0 {
		_ = s.Flush(ctx, lines)
	}
}
