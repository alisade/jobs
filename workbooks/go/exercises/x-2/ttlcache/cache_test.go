package ttlcache

import (
	"context"
	"testing"
	"time"
)

func TestSetGet(t *testing.T) {
	c := New[string, RegistryEntry](Options{TTL: time.Minute, Clock: newFakeClock()})
	c.Set("registry.arclight.dev/mcp/k8s-tools:1.4", RegistryEntry{Digest: "sha256:aa", ToolCount: 3})
	got, ok := c.Get("registry.arclight.dev/mcp/k8s-tools:1.4")
	if !ok || got.Digest != "sha256:aa" {
		t.Fatalf("Get = %+v, %v", got, ok)
	}
	if _, ok := c.Get("missing"); ok {
		t.Fatal("missing key reported present")
	}
}

func TestGetOrLoadCachesValue(t *testing.T) {
	c := New[string, int](Options{TTL: time.Minute, Clock: newFakeClock()})
	calls := 0
	load := func(ctx context.Context, k string) (int, error) { calls++; return len(k), nil }
	for i := 0; i < 3; i++ {
		v, err := c.GetOrLoad(context.Background(), "abcd", load)
		if err != nil || v != 4 {
			t.Fatalf("GetOrLoad = %d, %v", v, err)
		}
	}
	if calls != 1 {
		t.Fatalf("loader called %d times, want 1", calls)
	}
}
