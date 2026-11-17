package consumer

import (
	"context"
	"errors"
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

// Apply applies one decoded event inside tx.
//
// TODO: this is the version from the first spike and it is not safe under at-least-once delivery:
//   - it does not dedupe by event_id (record it in the same transaction as the mutation)
//   - it applies stale edits and lets a late edit resurrect a deleted activity
//   - it moves the live counter on every delivery, including duplicates
func Apply(tx store.Tx, ev Event) error {
	switch ev.Type {
	case TypeLogged:
		tx.PutActivity(store.Entry{ActivityID: ev.ActivityID, AccountID: ev.AccountID, Subject: ev.Subject, Version: ev.Version, OccurredAt: ev.OccurredAt})
		tx.AddCount(ev.AccountID, 1)
	case TypeEdited:
		cur, _ := tx.Activity(ev.ActivityID)
		cur.ActivityID, cur.AccountID, cur.Subject, cur.Version = ev.ActivityID, ev.AccountID, ev.Subject, ev.Version
		tx.PutActivity(cur)
	case TypeDeleted:
		cur, _ := tx.Activity(ev.ActivityID)
		cur.Deleted, cur.Version = true, ev.Version
		tx.PutActivity(cur)
		tx.AddCount(ev.AccountID, -1)
	}
	return nil
}

// HandleRecord processes one record: decode, apply in a transaction, retry transient failures,
// park what cannot be applied on the DLQ. It returns nil when the record is done (applied,
// skipped or parked) and the offset may be committed, and an error when it must not be.
//
// TODO: retries, DLQ, poison handling.
func (c *Consumer) HandleRecord(ctx context.Context, rec eventlog.Record) error {
	ev, err := Decode(rec.Value)
	if err != nil {
		return err
	}
	return c.Store.Apply(ctx, func(tx store.Tx) error { return Apply(tx, ev) })
}

// RunPartition consumes one partition until ctx is cancelled or a commit fails.
//
// TODO: commit after the record is handled (not before), and on shutdown finish the in-flight
// record (its apply and commit) instead of abandoning it halfway.
func (c *Consumer) RunPartition(ctx context.Context, g *eventlog.Group, r *eventlog.Reader) error {
	for {
		rec, err := r.Poll(ctx)
		if err != nil {
			return err
		}
		if err := g.Commit(rec.Partition, rec.Offset+1); err != nil {
			return err
		}
		if err := c.HandleRecord(ctx, rec); err != nil {
			return err
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
