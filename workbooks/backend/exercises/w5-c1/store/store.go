// Package store is the timeline consumer's database, modelled as an in-memory store with real
// transactions: Apply runs fn against a private copy and publishes all of its writes or none.
// Think of Apply as BEGIN ... COMMIT on Postgres. Provided infrastructure: no changes needed.
package store

import (
	"context"
	"errors"
	"sort"
	"sync"
	"time"
)

// Entry is one activity on an account timeline. Deleted entries are tombstones that keep their
// version so a late edit cannot resurrect them.
type Entry struct {
	ActivityID string
	AccountID  string
	Subject    string
	Version    int
	Deleted    bool
	OccurredAt time.Time
}

// Tx is the view of the store inside one transaction.
type Tx interface {
	// Processed reports whether an event id was already applied.
	Processed(eventID string) bool
	// MarkProcessed records an event id as applied.
	MarkProcessed(eventID string)
	// Activity returns the current entry (including tombstones).
	Activity(activityID string) (Entry, bool)
	// PutActivity inserts or replaces an entry.
	PutActivity(e Entry)
	// AddCount adjusts the account's live activity counter (shown on the account page).
	AddCount(accountID string, delta int)
}

// Store runs transactions.
type Store interface {
	Apply(ctx context.Context, fn func(Tx) error) error
}

// ErrTransient is the kind of error a real database returns for a serialization failure or a
// dropped connection: the transaction did not commit and may be retried.
var ErrTransient = errors.New("store: transient failure, transaction rolled back")

// Mem is an in-memory Store with all-or-nothing transactions.
type Mem struct {
	txMu      sync.Mutex // serializes whole transactions
	mu        sync.Mutex
	processed map[string]bool
	acts      map[string]Entry
	counts    map[string]int
	applies   int
	// BeforeCommit, if set, runs after fn succeeded and before the writes are published. A
	// non-nil error rolls the transaction back. Tests use it to inject failures or to block.
	BeforeCommit func(ctx context.Context, eventIDs []string) error
}

// NewMem returns an empty store.
func NewMem() *Mem {
	return &Mem{processed: map[string]bool{}, acts: map[string]Entry{}, counts: map[string]int{}}
}

type memTx struct {
	base      *Mem
	processed map[string]bool
	acts      map[string]Entry
	counts    map[string]int
	marked    []string
}

func (t *memTx) Processed(id string) bool {
	if v, ok := t.processed[id]; ok {
		return v
	}
	return t.base.processed[id]
}
func (t *memTx) MarkProcessed(id string) { t.processed[id] = true; t.marked = append(t.marked, id) }
func (t *memTx) Activity(id string) (Entry, bool) {
	if e, ok := t.acts[id]; ok {
		return e, true
	}
	e, ok := t.base.acts[id]
	return e, ok
}
func (t *memTx) PutActivity(e Entry) { t.acts[e.ActivityID] = e }
func (t *memTx) AddCount(acc string, d int) { t.counts[acc] += d }

// Apply runs fn in a transaction. Transactions are serialized (one at a time).
func (m *Mem) Apply(ctx context.Context, fn func(Tx) error) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	m.txMu.Lock()
	defer m.txMu.Unlock()
	tx := &memTx{base: m, processed: map[string]bool{}, acts: map[string]Entry{}, counts: map[string]int{}}
	m.mu.Lock()
	err := fn(tx)
	hook := m.BeforeCommit
	m.mu.Unlock()
	if err != nil {
		return err
	}
	if hook != nil {
		if err := hook(ctx, tx.marked); err != nil {
			return err
		}
	}
	m.mu.Lock()
	defer m.mu.Unlock()
	for k, v := range tx.processed {
		m.processed[k] = v
	}
	for k, v := range tx.acts {
		m.acts[k] = v
	}
	for k, v := range tx.counts {
		m.counts[k] += v
	}
	m.applies++
	return nil
}

// Timeline returns the live (not deleted) entries for an account, oldest first.
func (m *Mem) Timeline(accountID string) []Entry {
	m.mu.Lock()
	defer m.mu.Unlock()
	var out []Entry
	for _, e := range m.acts {
		if e.AccountID == accountID && !e.Deleted {
			out = append(out, e)
		}
	}
	sort.Slice(out, func(i, j int) bool {
		if !out[i].OccurredAt.Equal(out[j].OccurredAt) {
			return out[i].OccurredAt.Before(out[j].OccurredAt)
		}
		return out[i].ActivityID < out[j].ActivityID
	})
	return out
}

// Activity returns an entry outside a transaction (tests and the API).
func (m *Mem) Activity(id string) (Entry, bool) {
	m.mu.Lock()
	defer m.mu.Unlock()
	e, ok := m.acts[id]
	return e, ok
}

// Count returns the account's live activity counter.
func (m *Mem) Count(accountID string) int {
	m.mu.Lock()
	defer m.mu.Unlock()
	return m.counts[accountID]
}

// Processed reports whether an event id is recorded as applied.
func (m *Mem) Processed(eventID string) bool {
	m.mu.Lock()
	defer m.mu.Unlock()
	return m.processed[eventID]
}

// Applies returns the number of committed transactions.
func (m *Mem) Applies() int {
	m.mu.Lock()
	defer m.mu.Unlock()
	return m.applies
}
