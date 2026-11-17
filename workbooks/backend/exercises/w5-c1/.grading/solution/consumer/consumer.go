package consumer

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"

	"keystone/timeline/eventlog"
	"keystone/timeline/store"
)

// DLQ is where messages go that cannot be applied.
type DLQ interface {
	Send(ctx context.Context, rec eventlog.Record, attempts int, reason error) error
}

// Consumer builds account timelines from the activity topic.
type Consumer struct {
	Store       store.Store
	DLQ         DLQ
	MaxAttempts int           // total attempts for a transient failure before the DLQ (default 3)
	Backoff     time.Duration // pause between attempts (default 5ms)
}

func (c *Consumer) maxAttempts() int {
	if c.MaxAttempts <= 0 {
		return 3
	}
	return c.MaxAttempts
}

func (c *Consumer) backoff() time.Duration {
	if c.Backoff <= 0 {
		return 5 * time.Millisecond
	}
	return c.Backoff
}

func live(e store.Entry, ok bool) int {
	if ok && !e.Deleted {
		return 1
	}
	return 0
}

// Apply applies one decoded event inside tx. It is idempotent: the event id is recorded in the
// same transaction as the mutation, and every mutation is guarded by the activity version, so
// duplicates, redeliveries and stale or late events are no-ops.
func Apply(tx store.Tx, ev Event) error {
	if tx.Processed(ev.EventID) {
		return nil
	}
	tx.MarkProcessed(ev.EventID)
	cur, ok := tx.Activity(ev.ActivityID)
	if ok && cur.Version >= ev.Version {
		return nil // stale or already superseded (includes a late edit after a delete)
	}
	before := live(cur, ok)
	next := cur
	if !ok {
		next = store.Entry{ActivityID: ev.ActivityID, AccountID: ev.AccountID, OccurredAt: ev.OccurredAt}
	}
	next.Version = ev.Version
	switch ev.Type {
	case TypeLogged, TypeEdited:
		if ok && cur.Deleted {
			return nil // never resurrect a tombstone
		}
		next.Subject = ev.Subject
		if next.OccurredAt.IsZero() {
			next.OccurredAt = ev.OccurredAt
		}
	case TypeDeleted:
		next.Deleted = true
	default:
		return fmt.Errorf("%w: unknown type %q", ErrPoison, ev.Type)
	}
	tx.PutActivity(next)
	if d := live(next, true) - before; d != 0 {
		tx.AddCount(ev.AccountID, d)
	}
	return nil
}

// HandleRecord processes one record: decode, apply in a transaction, retry transient failures,
// park what cannot be applied on the DLQ. It returns nil when the record is done (applied,
// skipped or parked) and the offset may be committed, and an error when it must not be.
// The caller passes a context that is not cancelled by shutdown, so an in-flight record finishes.
func (c *Consumer) HandleRecord(ctx context.Context, rec eventlog.Record) error {
	ev, err := Decode(rec.Value)
	if err != nil {
		// A poison message never succeeds: park it now so the partition keeps moving.
		return c.DLQ.Send(ctx, rec, 1, err)
	}
	var last error
	for attempt := 1; attempt <= c.maxAttempts(); attempt++ {
		last = c.Store.Apply(ctx, func(tx store.Tx) error { return Apply(tx, ev) })
		if last == nil {
			return nil
		}
		if errors.Is(last, ErrPoison) {
			return c.DLQ.Send(ctx, rec, attempt, last)
		}
		if attempt < c.maxAttempts() {
			t := time.NewTimer(c.backoff() * time.Duration(attempt))
			select {
			case <-ctx.Done():
				t.Stop()
				return ctx.Err()
			case <-t.C:
			}
		}
	}
	return c.DLQ.Send(ctx, rec, c.maxAttempts(), last)
}

// RunPartition consumes one partition until ctx is cancelled or a commit fails. The offset is
// committed only after the record is handled; on shutdown the in-flight record is finished
// (apply and commit) and no new record is taken.
func (c *Consumer) RunPartition(ctx context.Context, g *eventlog.Group, r *eventlog.Reader) error {
	work := context.WithoutCancel(ctx)
	for {
		if ctx.Err() != nil {
			return nil
		}
		rec, err := r.Poll(ctx)
		if err != nil {
			if ctx.Err() != nil {
				return nil
			}
			return err
		}
		if err := c.HandleRecord(work, rec); err != nil {
			return fmt.Errorf("partition %d offset %d: %w", rec.Partition, rec.Offset, err)
		}
		if err := g.Commit(rec.Partition, rec.Offset+1); err != nil {
			return fmt.Errorf("commit partition %d offset %d: %w", rec.Partition, rec.Offset+1, err)
		}
	}
}

// Run consumes every partition of the log concurrently for group g and returns when all
// partition loops have stopped. It returns nil on a clean shutdown (ctx cancelled) and the
// first real error otherwise.
func (c *Consumer) Run(ctx context.Context, log *eventlog.Log, g *eventlog.Group) error {
	var wg sync.WaitGroup
	errs := make(chan error, log.Partitions())
	for p := 0; p < log.Partitions(); p++ {
		wg.Add(1)
		go func(p int) {
			defer wg.Done()
			if err := c.RunPartition(ctx, g, g.Reader(p)); err != nil && !errors.Is(err, context.Canceled) {
				errs <- err
			}
		}(p)
	}
	wg.Wait()
	close(errs)
	return <-errs
}
