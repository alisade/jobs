// Package eventlog is an in-memory stand-in for a Kafka/Redpanda topic: a fixed number of
// partitions, records keyed so one key always lands on one partition (per-key ordering), and
// consumer groups that commit the next offset to read. A new Reader starts from the group's
// committed offset, so anything read but not committed is delivered again (at-least-once).
// Provided infrastructure: you do not need to change this package.
package eventlog

import (
	"context"
	"errors"
	"hash/fnv"
	"sync"
)

// Record is one message on a partition.
type Record struct {
	Partition int
	Offset    int64
	Key       string
	Value     []byte
}

// Log is a topic with a fixed partition count.
type Log struct {
	mu     sync.Mutex
	parts  [][]Record
	notify chan struct{} // closed and replaced on every append
	groups map[string]*Group
}

// New returns a topic with n partitions.
func New(n int) *Log {
	if n < 1 {
		n = 1
	}
	return &Log{parts: make([][]Record, n), notify: make(chan struct{}), groups: map[string]*Group{}}
}

// Partitions returns the partition count.
func (l *Log) Partitions() int { return len(l.parts) }

// PartitionFor returns the partition a key maps to (FNV-1a, like a keyed producer).
func (l *Log) PartitionFor(key string) int {
	h := fnv.New32a()
	_, _ = h.Write([]byte(key))
	return int(h.Sum32() % uint32(len(l.parts)))
}

// Append writes a record to the key's partition. Appending the same value twice is how tests
// model a producer retry (a duplicate with the same event_id).
func (l *Log) Append(key string, value []byte) Record {
	p := l.PartitionFor(key)
	l.mu.Lock()
	r := Record{Partition: p, Offset: int64(len(l.parts[p])), Key: key, Value: append([]byte(nil), value...)}
	l.parts[p] = append(l.parts[p], r)
	close(l.notify)
	l.notify = make(chan struct{})
	l.mu.Unlock()
	return r
}

// End returns the next offset that would be written on partition p.
func (l *Log) End(p int) int64 {
	l.mu.Lock()
	defer l.mu.Unlock()
	return int64(len(l.parts[p]))
}

// Group returns (creating on first use) the consumer group with this name.
func (l *Log) Group(name string) *Group {
	l.mu.Lock()
	defer l.mu.Unlock()
	g, ok := l.groups[name]
	if !ok {
		g = &Group{log: l, committed: make([]int64, len(l.parts))}
		l.groups[name] = g
	}
	return g
}

// ErrCommitFailed is what a CommitHook returns to simulate a crash or a broker error at commit time.
var ErrCommitFailed = errors.New("eventlog: commit failed")

// Group holds committed offsets (next offset to read) per partition.
type Group struct {
	log       *Log
	mu        sync.Mutex
	committed []int64
	commits   int
	// CommitHook, if set, runs before a commit is recorded; a non-nil error rejects the commit.
	CommitHook func(partition int, next int64) error
}

// Committed returns the next offset the group will read on partition p.
func (g *Group) Committed(p int) int64 {
	g.mu.Lock()
	defer g.mu.Unlock()
	return g.committed[p]
}

// Commits returns how many commits succeeded (for tests).
func (g *Group) Commits() int {
	g.mu.Lock()
	defer g.mu.Unlock()
	return g.commits
}

// Commit records next as the next offset to read on partition p. Commits never move backwards.
func (g *Group) Commit(p int, next int64) error {
	g.mu.Lock()
	hook := g.CommitHook
	g.mu.Unlock()
	if hook != nil {
		if err := hook(p, next); err != nil {
			return err
		}
	}
	g.mu.Lock()
	defer g.mu.Unlock()
	if next > g.committed[p] {
		g.committed[p] = next
	}
	g.commits++
	return nil
}

// Reader returns a reader for partition p positioned at the group's committed offset.
func (g *Group) Reader(p int) *Reader {
	return &Reader{log: g.log, group: g, partition: p, pos: g.Committed(p)}
}

// Reader reads one partition sequentially. Not safe for concurrent use.
type Reader struct {
	log       *Log
	group     *Group
	partition int
	pos       int64
}

// Partition returns the partition this reader reads.
func (r *Reader) Partition() int { return r.partition }

// Poll blocks until the next record is available or ctx is done.
func (r *Reader) Poll(ctx context.Context) (Record, error) {
	for {
		r.log.mu.Lock()
		part := r.log.parts[r.partition]
		if r.pos < int64(len(part)) {
			rec := part[r.pos]
			r.pos++
			r.log.mu.Unlock()
			return rec, nil
		}
		wait := r.log.notify
		r.log.mu.Unlock()
		select {
		case <-ctx.Done():
			return Record{}, ctx.Err()
		case <-wait:
		}
	}
}
