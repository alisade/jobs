// Command loadprofile replays production-shaped traffic against the routing
// handler in-process and writes a CPU profile and a heap profile, the same
// profiles you would pull from :6060/debug/pprof in the cluster.
// It is run by `make setup` and `make profile`.
package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"math/rand/v2"
	"net/http"
	"net/http/httptest"
	"os"
	"runtime"
	"runtime/pprof"
	"sort"
	"sync"
	"sync/atomic"
	"time"

	"github.com/meridian/labelgate/router"
	"github.com/meridian/labelgate/server"
)

var teams = []string{"payments", "checkout", "search", "ledger", "fraud", "identity", "catalog", "shipping", "pricing", "notify", "billing", "reco"}

func body(rng *rand.Rand) []byte {
	tenant := teams[rng.IntN(len(teams))]
	req := server.RouteRequest{Tenant: tenant}
	for i := 0; i < 50; i++ {
		ns := tenant + "-prod"
		switch rng.IntN(10) {
		case 0:
			ns = tenant + "-stg" + fmt.Sprint(rng.IntN(3))
		case 1:
			ns = "kube-system"
		case 2:
			ns = "sandbox-" + fmt.Sprint(rng.IntN(40))
		}
		req.Series = append(req.Series, server.Series{Labels: map[string]string{
			"__name__":  []string{"http_requests_total", "http_request_duration_seconds_bucket", "process_cpu_seconds_total"}[rng.IntN(3)],
			"namespace": ns,
			"pod":       fmt.Sprintf("%s-api-%x-%05x", tenant, rng.IntN(16), rng.IntN(1<<20)),
			"job":       tenant + "-api",
			"instance":  fmt.Sprintf("10.42.%d.%d:8080", rng.IntN(64), rng.IntN(250)),
		}})
	}
	b, _ := json.Marshal(req)
	return b
}

func main() {
	rules := flag.String("rules", "config/rules.json", "rules file")
	cpuOut := flag.String("cpu", "artifacts/cpu.pprof", "cpu profile output")
	heapOut := flag.String("heap", "artifacts/heap.pprof", "heap profile output")
	dur := flag.Duration("for", 6*time.Second, "load duration")
	workers := flag.Int("c", 4, "concurrent clients")
	procs := flag.Int("procs", 4, "GOMAXPROCS, as in the pod (cpu limit 4)")
	flag.Parse()

	runtime.GOMAXPROCS(*procs)

	cfg, err := router.LoadConfig(*rules)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	r, err := router.New(cfg)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	h := server.Handler(r)

	// Pre-generate request bodies so the load generator does not dominate the profile.
	rng := rand.New(rand.NewPCG(42, 7))
	bodies := make([][]byte, 2000)
	for i := range bodies {
		bodies[i] = body(rng)
	}

	cf, err := os.Create(*cpuOut)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := pprof.StartCPUProfile(cf); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}

	var reqs atomic.Int64
	var mu sync.Mutex
	var lat []time.Duration
	deadline := time.Now().Add(*dur)
	var wg sync.WaitGroup
	for w := 0; w < *workers; w++ {
		wg.Add(1)
		go func(w int) {
			defer wg.Done()
			var local []time.Duration
			for i := w; time.Now().Before(deadline); i += *workers {
				req := httptest.NewRequest(http.MethodPost, "/api/v1/route", bytes.NewReader(bodies[i%len(bodies)]))
				rec := httptest.NewRecorder()
				t0 := time.Now()
				h.ServeHTTP(rec, req)
				local = append(local, time.Since(t0))
				if rec.Code != http.StatusOK {
					fmt.Fprintln(os.Stderr, "unexpected status", rec.Code, rec.Body.String())
					os.Exit(1)
				}
				reqs.Add(1)
			}
			mu.Lock()
			lat = append(lat, local...)
			mu.Unlock()
		}(w)
	}
	wg.Wait()
	pprof.StopCPUProfile()
	cf.Close()

	runtime.GC()
	hf, err := os.Create(*heapOut)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	_ = pprof.Lookup("heap").WriteTo(hf, 0)
	runtime.KeepAlive(r) // keep the router (and its cache) live for the heap profile
	hf.Close()

	sort.Slice(lat, func(i, j int) bool { return lat[i] < lat[j] })
	p := func(q float64) time.Duration { return lat[int(q*float64(len(lat)-1))] }
	fmt.Printf("loadprofile: %d requests (50 series each) in %s with %d clients: %.0f req/s  p50=%s p99=%s\n",
		reqs.Load(), *dur, *workers, float64(reqs.Load())/dur.Seconds(), p(0.50).Round(time.Microsecond), p(0.99).Round(time.Microsecond))
	fmt.Printf("loadprofile: wrote %s and %s\n", *cpuOut, *heapOut)
}
