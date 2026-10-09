// Package ttlcache is a sharded, generic TTL cache with load deduplication.
//
// The agent-fleet operator at Arclight resolves every MCPServer's upstream
// registry entry (image digest, allowed callers, tool manifest) on each
// reconcile. With 4,000 MCPServer objects and a 10-minute resync, the registry
// API is being hammered and rate-limits the operator. This cache sits in front
// of the registry client. See README.md for the full requirements.
package ttlcache

import (
	"context"
	"hash/maphash"
	"sync"
	"time"
)

// Clock is injected so tests can control time. A nil Clock means wall time.
type Clock interface {
	Now() time.Time
}

// Options configures a Cache. The zero value is usable: see the defaults.
type Options struct {
	Shards             int
	MaxEntriesPerShard int
	TTL                time.Duration
	Clock              Clock
}

// LoaderFunc loads the value for key on a miss.
type LoaderFunc[K comparable, V any] func(ctx context.Context, key K) (V, error)

type entry[V any] struct {
	value   V
	expires int64 // unix nanos; expired when expires <= now
}

// call is one in-flight load shared by every waiter for a key.
type call[V any] struct {
	done  chan struct{}
	value V
	err   error
}

type shard[K comparable, V any] struct {
	mu       sync.RWMutex
	items    map[K]entry[V]
	inflight map[K]*call[V]
}

// Cache is safe for concurrent use.
type Cache[K comparable, V any] struct {
	shards []*shard[K, V]
	mask   uint64
	seed   maphash.Seed
	max    int
	ttl    time.Duration
	clock  Clock
}

type wallClock struct{}

func (wallClock) Now() time.Time { return time.Now() }

// New builds a Cache with defaults applied.
func New[K comparable, V any](opts Options) *Cache[K, V] {
	n := opts.Shards
	if n <= 0 {
		n = 16
	}
	p := 1
	for p < n {
		p <<= 1
	}
	if opts.MaxEntriesPerShard <= 0 {
		opts.MaxEntriesPerShard = 1024
	}
	if opts.TTL <= 0 {
		opts.TTL = time.Minute
	}
	if opts.Clock == nil {
		opts.Clock = wallClock{}
	}
	c := &Cache[K, V]{
		shards: make([]*shard[K, V], p),
		mask:   uint64(p - 1),
		seed:   maphash.MakeSeed(),
		max:    opts.MaxEntriesPerShard,
		ttl:    opts.TTL,
		clock:  opts.Clock,
	}
	for i := range c.shards {
		c.shards[i] = &shard[K, V]{items: make(map[K]entry[V]), inflight: make(map[K]*call[V])}
	}
	return c
}

func (c *Cache[K, V]) shardFor(key K) *shard[K, V] {
	return c.shards[maphash.Comparable(c.seed, key)&c.mask]
}

func (c *Cache[K, V]) now() int64 { return c.clock.Now().UnixNano() }

// Get returns the value for key if present and not expired.
func (c *Cache[K, V]) Get(key K) (V, bool) {
	s := c.shardFor(key)
	now := c.now()
	s.mu.RLock()
	e, ok := s.items[key]
	s.mu.RUnlock()
	if !ok || e.expires <= now {
		var zero V
		return zero, false
	}
	return e.value, true
}

// Set stores value for key with a fresh TTL.
func (c *Cache[K, V]) Set(key K, value V) {
	s := c.shardFor(key)
	now := c.now()
	s.mu.Lock()
	c.storeLocked(s, key, value, now)
	s.mu.Unlock()
}

// storeLocked inserts with eviction; s.mu must be held for writing.
func (c *Cache[K, V]) storeLocked(s *shard[K, V], key K, value V, now int64) {
	if _, exists := s.items[key]; !exists && len(s.items) >= c.max {
		var victim K
		found := false
		var soonest int64
		for k, e := range s.items {
			if e.expires <= now { // expired: best possible victim
				victim, found = k, true
				break
			}
			if !found || e.expires < soonest {
				victim, soonest, found = k, e.expires, true
			}
		}
		if found {
			delete(s.items, victim)
		}
	}
	s.items[key] = entry[V]{value: value, expires: now + int64(c.ttl)}
}

// Delete removes key.
func (c *Cache[K, V]) Delete(key K) {
	s := c.shardFor(key)
	s.mu.Lock()
	delete(s.items, key)
	s.mu.Unlock()
}

// Len reports the number of stored entries.
func (c *Cache[K, V]) Len() int {
	n := 0
	for _, s := range c.shards {
		s.mu.RLock()
		n += len(s.items)
		s.mu.RUnlock()
	}
	return n
}

// GetOrLoad returns the cached value, or loads it with loader on a miss,
// sharing one load between concurrent callers for the same key.
func (c *Cache[K, V]) GetOrLoad(ctx context.Context, key K, loader LoaderFunc[K, V]) (V, error) {
	if v, ok := c.Get(key); ok {
		return v, nil
	}
	s := c.shardFor(key)
	s.mu.Lock()
	// Re-check under the write lock: another caller may have stored it.
	if e, ok := s.items[key]; ok && e.expires > c.now() {
		s.mu.Unlock()
		return e.value, nil
	}
	cl, loading := s.inflight[key]
	if !loading {
		cl = &call[V]{done: make(chan struct{})}
		s.inflight[key] = cl
		// Detach from the caller's cancellation: other waiters depend on this
		// load. Values (trace ids, loggers) are kept.
		go c.load(context.WithoutCancel(ctx), s, key, cl, loader)
	}
	s.mu.Unlock()

	select {
	case <-cl.done:
		return cl.value, cl.err
	case <-ctx.Done():
		var zero V
		return zero, ctx.Err()
	}
}

func (c *Cache[K, V]) load(ctx context.Context, s *shard[K, V], key K, cl *call[V], loader LoaderFunc[K, V]) {
	defer close(cl.done)
	cl.value, cl.err = loader(ctx, key)
	s.mu.Lock()
	delete(s.inflight, key)
	if cl.err == nil {
		c.storeLocked(s, key, cl.value, c.now())
	}
	s.mu.Unlock()
}
