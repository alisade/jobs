// Command repro replays the audit-sink incident against an in-process Kafka
// (kfake): it renders the replicas from deploy/audit-sink.yaml, builds each
// replica's config with sink.FromEnv, and runs them for ~15s with a
// CrashLoopBackOff-style restart when a replica exits. Run: make repro
package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"io"
	"log/slog"
	"os"
	"sync"
	"sync/atomic"
	"time"

	"github.com/twmb/franz-go/pkg/kfake"
	"github.com/twmb/franz-go/pkg/kgo"

	"github.com/relaypoint/audit-sink/internal/podsim"
	"github.com/relaypoint/audit-sink/internal/sink"
)

func main() {
	manifest := flag.String("manifest", "deploy/audit-sink.yaml", "workload manifest")
	dur := flag.Duration("for", 15*time.Second, "how long to run")
	records := flag.Int("records", 6000, "records to pre-load")
	flag.Parse()

	kind, reps, err := podsim.Render(*manifest, 1)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	fmt.Printf("workload kind=%s replicas=%d\n", kind, len(reps))

	cluster := kfake.MustCluster(kfake.NumBrokers(3), kfake.SeedTopics(6, "agent.audit"))
	defer cluster.Close()
	seed := cluster.ListenAddrs()

	prod, _ := kgo.NewClient(kgo.SeedBrokers(seed...), kgo.DefaultProduceTopic("agent.audit"))
	for i := 0; i < *records; i++ {
		prod.Produce(context.Background(), &kgo.Record{Value: []byte(fmt.Sprintf(`{"seq":%d}`, i))}, nil)
	}
	if err := prod.Flush(context.Background()); err != nil {
		fmt.Fprintln(os.Stderr, "preload:", err)
		os.Exit(2)
	}
	prod.Close()

	ctx, cancel := context.WithTimeout(context.Background(), *dur)
	defer cancel()
	start := time.Now()
	ts := func() string { return fmt.Sprintf("+%05.2fs", time.Since(start).Seconds()) }

	var consumed, fenced, restarts, assigns atomic.Int64
	quiet := slog.New(slog.NewTextHandler(io.Discard, nil))
	var wg sync.WaitGroup
	for _, rep := range reps {
		wg.Add(1)
		go func(rep podsim.Replica) {
			defer wg.Done()
			backoff := 250 * time.Millisecond
			for attempt := 0; ctx.Err() == nil; attempt++ {
				env := rep.Env
				env["KAFKA_BROKERS"] = seed[0]
				env["POD_NAME"] = rep.PodName
				cfg, err := sink.FromEnv(func(k string) string { return env[k] })
				if err != nil {
					fmt.Printf("%s %-28s config error: %v (CrashLoopBackOff)\n", ts(), rep.PodName, err)
					return
				}
				if attempt == 0 {
					fmt.Printf("%s %-28s start group.instance.id=%q\n", ts(), rep.PodName, cfg.InstanceID)
				}
				opts := append(cfg.Opts(),
					kgo.OnPartitionsAssigned(func(_ context.Context, _ *kgo.Client, m map[string][]int32) {
						assigns.Add(1)
						fmt.Printf("%s %-28s assigned %v\n", ts(), rep.PodName, m["agent.audit"])
					}),
					kgo.OnPartitionsRevoked(func(_ context.Context, _ *kgo.Client, m map[string][]int32) {
						if len(m["agent.audit"]) > 0 && ctx.Err() == nil {
							fmt.Printf("%s %-28s revoked %v\n", ts(), rep.PodName, m["agent.audit"])
						}
					}),
				)
				cl, err := kgo.NewClient(opts...)
				if err != nil {
					fmt.Println(err)
					return
				}
				err = sink.Run(ctx, cl, quiet, func(*kgo.Record) error {
					consumed.Add(1)
					time.Sleep(200 * time.Microsecond) // indexing cost
					return nil
				})
				cl.Close()
				if errors.Is(err, sink.ErrFenced) {
					fenced.Add(1)
					restarts.Add(1)
					fmt.Printf("%s %-28s exit 1: %v; kubelet restart in %s\n", ts(), rep.PodName, err, backoff)
					select {
					case <-ctx.Done():
					case <-time.After(backoff):
					}
					if backoff < 2*time.Second {
						backoff *= 2
					}
					continue
				}
				return
			}
		}(rep)
	}
	wg.Wait()
	fmt.Println("---- summary ----")
	fmt.Printf("records processed (incl. re-deliveries): %d, preloaded: %d\n", consumed.Load(), *records)
	fmt.Printf("partition assignments: %d, fenced exits: %d, restarts: %d\n", assigns.Load(), fenced.Load(), restarts.Load())
}
