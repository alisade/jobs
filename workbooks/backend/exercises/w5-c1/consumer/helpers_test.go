package consumer

import (
	"context"
	"fmt"
	"testing"
	"time"

	"keystone/timeline/eventlog"
	"keystone/timeline/store"
)

var t0 = time.Date(2026, 11, 2, 9, 0, 0, 0, time.UTC)

func ev(id, typ, account, activity string, version int, subject string) Event {
	return Event{EventID: id, Type: typ, AccountID: account, ActivityID: activity, Version: version, Subject: subject,
		OccurredAt: t0.Add(time.Duration(version) * time.Minute)}
}

func publish(l *eventlog.Log, events ...Event) {
	for _, e := range events {
		l.Append(e.AccountID, Encode(e))
	}
}

type rig struct {
	log   *eventlog.Log
	group *eventlog.Group
	store *store.Mem
	dlq   *store.MemDLQ
	c     *Consumer
}

func newRig(partitions int) *rig {
	l := eventlog.New(partitions)
	s := store.NewMem()
	d := &store.MemDLQ{}
	return &rig{log: l, group: l.Group("timeline"), store: s, dlq: d,
		c: &Consumer{Store: s, DLQ: d, Backoff: time.Millisecond}}
}

// start runs the consumer in the background; stop cancels it and waits (bounded).
func (r *rig) start(t *testing.T) (stop func() error, done <-chan error) {
	t.Helper()
	ctx, cancel := context.WithCancel(context.Background())
	ch := make(chan error, 1)
	go func() { ch <- r.c.Run(ctx, r.log, r.group) }()
	return func() error {
		cancel()
		select {
		case err := <-ch:
			return err
		case <-time.After(3 * time.Second):
			t.Fatal("consumer did not stop within 3s after cancel")
			return nil
		}
	}, ch
}

// caughtUp reports whether the group has committed everything on every partition.
func (r *rig) caughtUp() bool {
	for p := 0; p < r.log.Partitions(); p++ {
		if r.group.Committed(p) < r.log.End(p) {
			return false
		}
	}
	return true
}

func waitFor(t *testing.T, what string, cond func() bool) {
	t.Helper()
	deadline := time.Now().Add(3 * time.Second)
	for time.Now().Before(deadline) {
		if cond() {
			return
		}
		time.Sleep(2 * time.Millisecond)
	}
	t.Fatalf("timed out after 3s waiting for: %s", what)
}

func subjects(es []store.Entry) string {
	out := ""
	for _, e := range es {
		out += fmt.Sprintf("[%s v%d %q]", e.ActivityID, e.Version, e.Subject)
	}
	return out
}
