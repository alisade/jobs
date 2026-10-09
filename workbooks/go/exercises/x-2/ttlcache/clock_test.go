package ttlcache

import (
	"sync"
	"time"
)

// fakeClock is a manually advanced Clock for tests.
type fakeClock struct {
	mu  sync.Mutex
	now time.Time
}

func newFakeClock() *fakeClock { return &fakeClock{now: time.Date(2026, 5, 1, 9, 0, 0, 0, time.UTC)} }

func (f *fakeClock) Now() time.Time {
	f.mu.Lock()
	defer f.mu.Unlock()
	return f.now
}

func (f *fakeClock) Advance(d time.Duration) {
	f.mu.Lock()
	f.now = f.now.Add(d)
	f.mu.Unlock()
}

// RegistryEntry is what the operator caches per MCPServer image.
type RegistryEntry struct {
	Digest         string
	AllowedCallers []string
	ToolCount      int
}
