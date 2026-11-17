// Command replay runs the consumer over a small, messy event stream (duplicates, a stale edit,
// a late edit after a delete, a poison message) and prints the resulting timeline, so you can
// watch your consumer behave: go run ./cmd/replay
package main

import (
	"context"
	"fmt"
	"os"
	"time"

	"keystone/timeline/consumer"
	"keystone/timeline/eventlog"
	"keystone/timeline/store"
)

func main() {
	t0 := time.Date(2026, 11, 2, 9, 0, 0, 0, time.UTC)
	e := func(id, typ, act string, v int, subj string) consumer.Event {
		return consumer.Event{EventID: id, Type: typ, AccountID: "acc-0042", ActivityID: act, Version: v, Subject: subj, OccurredAt: t0.Add(time.Duration(v) * time.Minute)}
	}
	l := eventlog.New(2)
	stream := []consumer.Event{
		e("e1", consumer.TypeLogged, "call-1", 1, "Discovery call"),
		e("e1", consumer.TypeLogged, "call-1", 1, "Discovery call"),
		e("e3", consumer.TypeEdited, "call-1", 3, "Discovery call - final notes"),
		e("e2", consumer.TypeEdited, "call-1", 2, "Discovery call - draft"),
		e("e4", consumer.TypeLogged, "mail-1", 1, "Sent pricing"),
		e("e5", consumer.TypeDeleted, "mail-1", 2, ""),
		e("e6", consumer.TypeEdited, "mail-1", 2, "late edit"),
	}
	for _, ev := range stream {
		l.Append(ev.AccountID, consumer.Encode(ev))
	}
	l.Append("acc-0042", []byte("{not json"))
	s, d := store.NewMem(), &store.MemDLQ{}
	c := &consumer.Consumer{Store: s, DLQ: d, Backoff: time.Millisecond}
	g := l.Group("timeline")
	ctx, cancel := context.WithTimeout(context.Background(), 500*time.Millisecond)
	defer cancel()
	if err := c.Run(ctx, l, g); err != nil {
		fmt.Fprintln(os.Stderr, "run:", err)
	}
	fmt.Printf("live count acc-0042: %d (want 1)\n", s.Count("acc-0042"))
	for _, en := range s.Timeline("acc-0042") {
		fmt.Printf("  %s v%d %q\n", en.ActivityID, en.Version, en.Subject)
	}
	fmt.Printf("dlq: %d message(s) (want 1)\n", len(d.Messages()))
}
