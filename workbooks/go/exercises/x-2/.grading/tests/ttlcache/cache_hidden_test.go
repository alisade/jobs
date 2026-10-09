package ttlcache

import (
	"context"
	"errors"
	"fmt"
	"strconv"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

func TestHiddenTTLExpiryBoundary(t *testing.T) {
	clk := newFakeClock()
	c := New[string, int](Options{TTL: 30 * time.Second, Clock: clk})
	c.Set("a", 1)
	clk.Advance(29 * time.Second)
	if v, ok := c.Get("a"); !ok || v != 1 {
		t.Fatalf("at 29s: Get = %d, %v; want fresh", v, ok)
	}
	clk.Advance(time.Second)
	if _, ok := c.Get("a"); ok {
		t.Fatal("at exactly TTL the entry must be expired")
	}
}

func TestHiddenSetRefreshesTTLAndOverwrites(t *testing.T) {
	clk := newFakeClock()
	c := New[string, int](Options{TTL: 10 * time.Second, Clock: clk})
	c.Set("a", 1)
	clk.Advance(8 * time.Second)
	c.Set("a", 2)
	clk.Advance(8 * time.Second)
	if v, ok := c.Get("a"); !ok || v != 2 {
		t.Fatalf("Get = %d, %v; Set must overwrite and refresh the TTL", v, ok)
	}
}

func TestHiddenDeleteAndLen(t *testing.T) {
	c := New[string, int](Options{Clock: newFakeClock()})
	for i := 0; i < 10; i++ {
		c.Set(strconv.Itoa(i), i)
	}
	if c.Len() != 10 {
		t.Fatalf("Len = %d, want 10", c.Len())
	}
	c.Delete("3")
	c.Delete("not-there")
	if _, ok := c.Get("3"); ok || c.Len() != 9 {
		t.Fatalf("after Delete: present=%v Len=%d", ok, c.Len())
	}
}

func TestHiddenZeroOptionsUsable(t *testing.T) {
	c := New[int, string](Options{})
	c.Set(7, "seven")
	if v, ok := c.Get(7); !ok || v != "seven" {
		t.Fatalf("zero Options: Get = %q, %v (defaults: 16 shards, 1024/shard, 1m TTL, wall clock)", v, ok)
	}
}

func TestHiddenEvictionBound(t *testing.T) {
	c := New[string, int](Options{Shards: 3, MaxEntriesPerShard: 8, Clock: newFakeClock()}) // 3 rounds up to 4
	for i := 0; i < 2000; i++ {
		k := "k" + strconv.Itoa(i)
		c.Set(k, i)
		if _, ok := c.Get(k); !ok {
			t.Fatalf("key %s missing right after Set", k)
		}
	}
	if n := c.Len(); n > 4*8 {
		t.Fatalf("Len = %d, want <= 32 (4 shards x 8)", n)
	}
}

func TestHiddenEvictionPrefersExpired(t *testing.T) {
	clk := newFakeClock()
	c := New[string, int](Options{Shards: 1, MaxEntriesPerShard: 4, TTL: 60 * time.Second, Clock: clk})
	c.Set("old-1", 1)
	c.Set("old-2", 2)
	clk.Advance(50 * time.Second)
	c.Set("live-1", 3)
	c.Set("live-2", 4)
	clk.Advance(20 * time.Second) // old-* expired, live-* fresh
	c.Set("new", 5)
	for _, k := range []string{"live-1", "live-2", "new"} {
		if _, ok := c.Get(k); !ok {
			t.Fatalf("%s evicted while an expired entry was available", k)
		}
	}
	if c.Len() > 4 {
		t.Fatalf("Len = %d, want <= 4", c.Len())
	}
}

func TestHiddenEvictionClosestToExpiryWhenNoneExpired(t *testing.T) {
	clk := newFakeClock()
	c := New[string, int](Options{Shards: 1, MaxEntriesPerShard: 3, TTL: time.Minute, Clock: clk})
	c.Set("first", 1)
	clk.Advance(time.Second)
	c.Set("second", 2)
	clk.Advance(time.Second)
	c.Set("third", 3)
	clk.Advance(time.Second)
	c.Set("fourth", 4)
	if _, ok := c.Get("first"); ok {
		t.Fatal("the entry closest to expiry (first) should have been evicted")
	}
	for _, k := range []string{"second", "third", "fourth"} {
		if _, ok := c.Get(k); !ok {
			t.Fatalf("%s should still be present", k)
		}
	}
}

func TestHiddenGetOrLoadDeduplicates(t *testing.T) {
	c := New[string, RegistryEntry](Options{Clock: newFakeClock()})
	var calls atomic.Int32
	release := make(chan struct{})
	load := func(ctx context.Context, k string) (RegistryEntry, error) {
		calls.Add(1)
		<-release
		return RegistryEntry{Digest: "sha256:" + k}, nil
	}
	const n = 64
	var wg sync.WaitGroup
	results := make([]RegistryEntry, n)
	errs := make([]error, n)
	for i := 0; i < n; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			results[i], errs[i] = c.GetOrLoad(context.Background(), "img", load)
		}()
	}
	time.Sleep(50 * time.Millisecond) // let every caller pile up on the in-flight load
	close(release)
	waitOrFail(t, &wg, 10*time.Second)
	if got := calls.Load(); got != 1 {
		t.Fatalf("loader called %d times for %d concurrent callers, want 1", got, n)
	}
	for i := 0; i < n; i++ {
		if errs[i] != nil || results[i].Digest != "sha256:img" {
			t.Fatalf("caller %d: %+v, %v", i, results[i], errs[i])
		}
	}
	if v, ok := c.Get("img"); !ok || v.Digest != "sha256:img" {
		t.Fatal("loaded value not cached")
	}
}

func TestHiddenLoadErrorSharedNotCached(t *testing.T) {
	c := New[string, int](Options{Clock: newFakeClock()})
	boom := errors.New("registry: 429 too many requests")
	var calls atomic.Int32
	release := make(chan struct{})
	load := func(ctx context.Context, k string) (int, error) {
		calls.Add(1)
		<-release
		return 0, fmt.Errorf("lookup %s: %w", k, boom)
	}
	var wg sync.WaitGroup
	var errCount atomic.Int32
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if _, err := c.GetOrLoad(context.Background(), "k", load); errors.Is(err, boom) {
				errCount.Add(1)
			}
		}()
	}
	time.Sleep(30 * time.Millisecond)
	close(release)
	waitOrFail(t, &wg, 10*time.Second)
	if calls.Load() != 1 || errCount.Load() != 10 {
		t.Fatalf("calls=%d callers-with-error=%d; want 1 and 10 (error shared, wrapped)", calls.Load(), errCount.Load())
	}
	ok := func(ctx context.Context, k string) (int, error) { calls.Add(1); return 42, nil }
	v, err := c.GetOrLoad(context.Background(), "k", ok)
	if err != nil || v != 42 || calls.Load() != 2 {
		t.Fatalf("after an error the next call must load again: v=%d err=%v calls=%d", v, err, calls.Load())
	}
}

func TestHiddenWaiterCancellationDoesNotCancelLoad(t *testing.T) {
	c := New[string, int](Options{Clock: newFakeClock()})
	started := make(chan struct{})
	release := make(chan struct{})
	var loaderCtxErr atomic.Value
	load := func(ctx context.Context, k string) (int, error) {
		close(started)
		<-release
		loaderCtxErr.Store(fmt.Sprint(ctx.Err()))
		return 7, nil
	}
	// Caller A starts the load and then gives up.
	ctxA, cancelA := context.WithCancel(context.Background())
	errA := make(chan error, 1)
	go func() {
		_, err := c.GetOrLoad(ctxA, "k", load)
		errA <- err
	}()
	select {
	case <-started:
	case <-time.After(2 * time.Second):
		t.Fatal("GetOrLoad never called the loader")
	}
	// Caller B waits on the same load with a live context.
	resB := make(chan int, 1)
	go func() {
		v, _ := c.GetOrLoad(context.Background(), "k", load)
		resB <- v
	}()
	time.Sleep(20 * time.Millisecond)
	cancelA()
	select {
	case err := <-errA:
		if !errors.Is(err, context.Canceled) {
			t.Fatalf("caller A: err = %v, want context.Canceled", err)
		}
	case <-time.After(time.Second):
		t.Fatal("cancelled caller did not return promptly")
	}
	close(release)
	select {
	case v := <-resB:
		if v != 7 {
			t.Fatalf("caller B got %d, want 7", v)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("caller B never got the value")
	}
	if got := loaderCtxErr.Load(); got != "<nil>" {
		t.Fatalf("loader ctx was cancelled (%v): one caller giving up must not cancel the shared load", got)
	}
}

func TestHiddenDifferentKeysLoadConcurrently(t *testing.T) {
	c := New[string, int](Options{Shards: 1, Clock: newFakeClock()}) // same shard on purpose
	var barrier sync.WaitGroup
	barrier.Add(2)
	load := func(ctx context.Context, k string) (int, error) {
		barrier.Done()
		barrier.Wait() // deadlocks if loads are serialized
		return len(k), nil
	}
	done := make(chan struct{})
	go func() {
		var wg sync.WaitGroup
		for _, k := range []string{"a", "bb"} {
			wg.Add(1)
			go func() { defer wg.Done(); _, _ = c.GetOrLoad(context.Background(), k, load) }()
		}
		wg.Wait()
		close(done)
	}()
	select {
	case <-done:
	case <-time.After(2 * time.Second):
		t.Fatal("loads for different keys are serialized (do not hold a lock while loading)")
	}
}

func TestHiddenReloadAfterExpiry(t *testing.T) {
	clk := newFakeClock()
	c := New[string, int](Options{TTL: time.Minute, Clock: clk})
	var calls atomic.Int32
	load := func(ctx context.Context, k string) (int, error) { return int(calls.Add(1)), nil }
	v1, _ := c.GetOrLoad(context.Background(), "k", load)
	clk.Advance(2 * time.Minute)
	v2, _ := c.GetOrLoad(context.Background(), "k", load)
	if v1 != 1 || v2 != 2 {
		t.Fatalf("v1=%d v2=%d; an expired entry must be reloaded", v1, v2)
	}
}

func TestHiddenConcurrentMixedOpsRaceFree(t *testing.T) {
	c := New[int, string](Options{Shards: 4, MaxEntriesPerShard: 16, TTL: time.Second})
	load := func(ctx context.Context, k int) (string, error) { return strconv.Itoa(k), nil }
	var wg sync.WaitGroup
	for g := 0; g < 12; g++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for i := 0; i < 2000; i++ {
				k := (i * (g + 1)) % 200
				switch i % 4 {
				case 0:
					c.Set(k, "x")
				case 1:
					c.Get(k)
				case 2:
					if v, err := c.GetOrLoad(context.Background(), k, load); err != nil || (v != "x" && v != strconv.Itoa(k)) {
						t.Errorf("GetOrLoad(%d) = %q, %v", k, v, err)
						return
					}
				case 3:
					c.Delete(k)
				}
			}
		}()
	}
	waitOrFail(t, &wg, 10*time.Second)
	if c.Len() > 64 {
		t.Fatalf("Len = %d, want <= 64", c.Len())
	}
}

func TestHiddenGetHitDoesNotAllocate(t *testing.T) {
	c := New[string, RegistryEntry](Options{TTL: time.Hour})
	key := "registry.arclight.dev/mcp/k8s-tools:1.4"
	c.Set(key, RegistryEntry{Digest: "sha256:aa", AllowedCallers: []string{"agent-runtime"}})
	if a := testing.AllocsPerRun(1000, func() { c.Get(key) }); a != 0 {
		t.Fatalf("Get hit: %.1f allocs/op, want 0", a)
	}
	type key2 struct {
		NS, Name string
		Gen      int64
	}
	c2 := New[key2, int](Options{TTL: time.Hour})
	k2 := key2{"agents", "k8s-tools", 3}
	c2.Set(k2, 1)
	if a := testing.AllocsPerRun(1000, func() { c2.Get(k2) }); a != 0 {
		t.Fatalf("Get hit with a struct key: %.1f allocs/op, want 0", a)
	}
	if _, ok := c2.Get(k2); !ok {
		t.Fatal("struct key not found")
	}
}

// waitOrFail bounds a WaitGroup wait so a deadlocked implementation fails this
// test instead of hanging the whole package until the go test timeout.
func waitOrFail(t *testing.T, wg *sync.WaitGroup, d time.Duration) {
	t.Helper()
	done := make(chan struct{})
	go func() { wg.Wait(); close(done) }()
	select {
	case <-done:
	case <-time.After(d):
		t.Fatalf("callers still blocked after %v: deadlock or a load that never completes", d)
	}
}
