package store

import (
	"context"
	"sync"

	"keystone/timeline/eventlog"
)

// DeadLetter is one message parked on the dead-letter topic (activity.timeline.dlq).
type DeadLetter struct {
	Record   eventlog.Record
	Attempts int
	Reason   string
}

// MemDLQ is an in-memory dead-letter topic.
type MemDLQ struct {
	mu   sync.Mutex
	msgs []DeadLetter
}

// Send parks a record with the number of attempts made and the last error.
func (d *MemDLQ) Send(_ context.Context, rec eventlog.Record, attempts int, reason error) error {
	d.mu.Lock()
	defer d.mu.Unlock()
	msg := ""
	if reason != nil {
		msg = reason.Error()
	}
	d.msgs = append(d.msgs, DeadLetter{Record: rec, Attempts: attempts, Reason: msg})
	return nil
}

// Messages returns a copy of everything parked so far.
func (d *MemDLQ) Messages() []DeadLetter {
	d.mu.Lock()
	defer d.mu.Unlock()
	return append([]DeadLetter(nil), d.msgs...)
}
