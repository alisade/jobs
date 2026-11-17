// Command repro drives the shipper against a fake bulk endpoint that is slow
// and ignores context (like the vendor SDK during an OpenSearch brownout),
// then writes a goroutine profile to artifacts/goroutines-live.txt.
// It is run by `make setup`.
package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"runtime"
	"runtime/pprof"
	"sync"
	"time"

	"github.com/tidewater/driftwood/shipper"
)

type brownoutSink struct{ delay time.Duration }

func (b brownoutSink) Send(ctx context.Context, p []byte) error {
	time.Sleep(b.delay) // the vendor client ignores ctx
	return nil
}

func main() {
	out := flag.String("out", "artifacts/goroutines-live.txt", "where to write the goroutine profile")
	dur := flag.Duration("for", 3*time.Second, "how long to run")
	flag.Parse()

	s := shipper.New(brownoutSink{delay: 200 * time.Millisecond}, shipper.Config{
		SendTimeout: 50 * time.Millisecond, MaxRetries: 1, Backoff: 10 * time.Millisecond,
	})
	before := runtime.NumGoroutine()
	ctx, cancel := context.WithTimeout(context.Background(), *dur)
	defer cancel()

	var wg sync.WaitGroup
	for w := 0; w < 8; w++ { // one tailer per log file
		wg.Add(1)
		go func() {
			defer wg.Done()
			for ctx.Err() == nil {
				_ = s.Flush(ctx, []string{`{"level":"info","msg":"request served","status":200}`})
			}
		}()
	}
	wg.Wait()
	time.Sleep(time.Second) // every sink call has returned by now
	after := runtime.NumGoroutine()

	f, err := os.Create(*out)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	defer f.Close()
	fmt.Fprintf(f, "# driftwood repro: %s of brownout, 8 tailers, SendTimeout=50ms\n", *dur)
	fmt.Fprintf(f, "# goroutines before=%d after all Flush calls returned=%d\n", before, after)
	fmt.Fprintf(f, "# batches sent=%d failed=%d attempts=%d timeouts=%d\n",
		s.Stats.BatchesSent.Load(), s.Stats.BatchesFailed.Load(), s.Stats.Attempts.Load(), s.Stats.Timeouts.Load())
	fmt.Fprintf(f, "# profile below is /debug/pprof/goroutine?debug=1 (grouped by identical stack)\n\n")
	if err := pprof.Lookup("goroutine").WriteTo(f, 1); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Printf("repro: goroutines before=%d after=%d -> %s\n", before, after, *out)
}
