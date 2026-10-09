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
	"errors"
	"time"
)

// Clock is injected so tests can control time. A nil Clock means wall time.
type Clock interface {
	Now() time.Time
}

// Options configures a Cache. The zero value is usable: see the defaults.
type Options struct {
	// Shards is the number of independently locked shards; rounded up to a
	// power of two. Default 16.
	Shards int
	// MaxEntriesPerShard bounds memory. When a shard is full, inserting a new
	// key evicts an expired entry if there is one, otherwise the entry closest
	// to expiry. Default 1024.
	MaxEntriesPerShard int
	// TTL is how long a Set or loaded value stays fresh. Default 1 minute.
	TTL time.Duration
	// Clock defaults to wall time.
	Clock Clock
}

// LoaderFunc loads the value for key on a miss.
type LoaderFunc[K comparable, V any] func(ctx context.Context, key K) (V, error)

// ErrNotImplemented is returned by the starter stubs. Delete it when done.
var ErrNotImplemented = errors.New("ttlcache: not implemented")

// Cache is safe for concurrent use.
type Cache[K comparable, V any] struct {
	// TODO: shards, hashing seed, options.
}

// New builds a Cache with defaults applied.
func New[K comparable, V any](opts Options) *Cache[K, V] {
	// TODO
	return &Cache[K, V]{}
}

// Get returns the value for key if present and not expired. A hit must not
// allocate.
func (c *Cache[K, V]) Get(key K) (V, bool) {
	// TODO
	var zero V
	return zero, false
}

// Set stores value for key with a fresh TTL.
func (c *Cache[K, V]) Set(key K, value V) {
	// TODO
}

// Delete removes key. Deleting a missing key is a no-op.
func (c *Cache[K, V]) Delete(key K) {
	// TODO
}

// Len reports the number of stored entries (expired entries that have not been
// removed yet may be counted).
func (c *Cache[K, V]) Len() int {
	// TODO
	return 0
}

// GetOrLoad returns the cached value, or loads it with loader on a miss.
//
//   - Concurrent callers for the same missing key share ONE loader call.
//   - A successful result is cached with the TTL; an error is returned to every
//     caller waiting on that load and is NOT cached.
//   - If a caller's ctx is done while it waits, that caller returns ctx.Err()
//     promptly; the load continues for the other waiters and its ctx is not
//     cancelled by any single caller.
//   - Loads for different keys run concurrently.
func (c *Cache[K, V]) GetOrLoad(ctx context.Context, key K, loader LoaderFunc[K, V]) (V, error) {
	// TODO
	var zero V
	return zero, ErrNotImplemented
}
