package ttlcache

import (
	"context"
	"strconv"
	"testing"
	"time"
)

// go test -run XXX -bench . -benchmem ./ttlcache
func BenchmarkGetHit(b *testing.B) {
	c := New[string, RegistryEntry](Options{TTL: time.Hour})
	keys := make([]string, 1024)
	for i := range keys {
		keys[i] = "registry.arclight.dev/mcp/server-" + strconv.Itoa(i)
		c.Set(keys[i], RegistryEntry{Digest: "sha256:" + strconv.Itoa(i)})
	}
	b.ReportAllocs()
	i := 0
	for b.Loop() {
		c.Get(keys[i&1023])
		i++
	}
}

func BenchmarkGetParallel(b *testing.B) {
	c := New[string, RegistryEntry](Options{TTL: time.Hour})
	keys := make([]string, 1024)
	for i := range keys {
		keys[i] = "registry.arclight.dev/mcp/server-" + strconv.Itoa(i)
		c.Set(keys[i], RegistryEntry{Digest: "sha256:" + strconv.Itoa(i)})
	}
	b.ReportAllocs()
	b.RunParallel(func(pb *testing.PB) {
		i := 0
		for pb.Next() {
			c.Get(keys[i&1023])
			i++
		}
	})
}

func BenchmarkGetOrLoadParallel(b *testing.B) {
	c := New[int, int](Options{TTL: time.Hour, MaxEntriesPerShard: 64})
	load := func(ctx context.Context, k int) (int, error) { return k * 2, nil }
	b.ReportAllocs()
	b.RunParallel(func(pb *testing.PB) {
		i := 0
		for pb.Next() {
			_, _ = c.GetOrLoad(context.Background(), i&4095, load)
			i++
		}
	})
}
