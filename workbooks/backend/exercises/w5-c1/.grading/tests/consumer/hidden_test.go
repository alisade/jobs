package consumer

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"keystone/timeline/eventlog"
	"keystone/timeline/store"
)

func TestHiddenDuplicateDeliveryAppliesOnce(t *testing.T) {
	r := newRig(1)
	e := ev("e1", TypeLogged, "acc-1", "act-1", 1, "Discovery call")
	publish(r.log, e, e, e) // producer retries
	stop, _ := r.start(t)
	waitFor(t, "caught up", r.caughtUp)
	_ = stop()
	if c := r.store.Count("acc-1"); c != 1 {
		t.Fatalf("live count = %d after 3 deliveries of one event, want 1", c)
	}
	if !r.store.Processed("e1") {
		t.Fatal("event e1 is not recorded as processed in the store")
	}
}

func TestHiddenCommitOnlyAfterApply(t *testing.T) {
	r := newRig(1)
	publish(r.log, ev("e1", TypeLogged, "acc-1", "act-1", 1, "a"), ev("e2", TypeLogged, "acc-1", "act-2", 1, "b"))
	var violations int32
	r.store.BeforeCommit = func(_ context.Context, _ []string) error {
		// e2 is offset 1: while its transaction commits, the group must not have committed past it.
		if r.group.Committed(0) > 1 {
			atomic.AddInt32(&violations, 1)
		}
		return nil
	}
	stop, _ := r.start(t)
	waitFor(t, "caught up", r.caughtUp)
	_ = stop()
	if v := atomic.LoadInt32(&violations); v != 0 {
		t.Fatalf("offset was committed before the record's transaction committed (%d times): a crash there loses the event", v)
	}
}

func TestHiddenRedeliveryAfterCrashBetweenApplyAndCommit(t *testing.T) {
	r := newRig(1)
	publish(r.log, ev("e1", TypeLogged, "acc-1", "act-1", 1, "a"), ev("e2", TypeLogged, "acc-1", "act-2", 1, "b"), ev("e3", TypeLogged, "acc-1", "act-3", 1, "c"))
	var once sync.Once
	r.group.CommitHook = func(p int, next int64) error {
		crash := false
		if next == 2 {
			once.Do(func() { crash = true })
		}
		if crash {
			return eventlog.ErrCommitFailed
		}
		return nil
	}
	_, done := r.start(t)
	select {
	case err := <-done:
		if err == nil {
			t.Fatal("Run returned nil after a failed commit; it should stop with the error (the pod restarts)")
		}
	case <-time.After(3 * time.Second):
		t.Fatal("Run did not return after the commit failure")
	}
	// the pod restarts: new readers from the committed offset redeliver e2
	stop, _ := r.start(t)
	waitFor(t, "caught up after restart", r.caughtUp)
	_ = stop()
	if c := r.store.Count("acc-1"); c != 3 {
		t.Fatalf("live count = %d after redelivery, want 3 (each activity once)", c)
	}
}

func TestHiddenStaleEditIgnored(t *testing.T) {
	r := newRig(1)
	publish(r.log,
		ev("e1", TypeLogged, "acc-1", "act-1", 1, "Call"),
		ev("e3", TypeEdited, "acc-1", "act-1", 3, "Call - final notes"),
		ev("e2", TypeEdited, "acc-1", "act-1", 2, "Call - draft"),
	)
	stop, _ := r.start(t)
	waitFor(t, "caught up", r.caughtUp)
	_ = stop()
	e, ok := r.store.Activity("act-1")
	if !ok || e.Version != 3 || e.Subject != "Call - final notes" {
		t.Fatalf("act-1 = %+v, want version 3 with the final subject (stale v2 edit ignored)", e)
	}
	if r.store.Count("acc-1") != 1 {
		t.Fatalf("live count = %d, want 1 (edits do not change the count)", r.store.Count("acc-1"))
	}
}

func TestHiddenLateEditDoesNotResurrectDelete(t *testing.T) {
	r := newRig(1)
	edit := ev("e2", TypeEdited, "acc-1", "act-1", 2, "edited")
	publish(r.log,
		ev("e1", TypeLogged, "acc-1", "act-1", 1, "Call"),
		edit,
		ev("e3", TypeDeleted, "acc-1", "act-1", 3, ""),
		edit, // relay redelivers the edit after the delete
		ev("e4", TypeEdited, "acc-1", "act-1", 2, "edited again by a lagging client"),
	)
	stop, _ := r.start(t)
	waitFor(t, "caught up", r.caughtUp)
	_ = stop()
	if tl := r.store.Timeline("acc-1"); len(tl) != 0 {
		t.Fatalf("deleted activity came back: %s", subjects(tl))
	}
	if c := r.store.Count("acc-1"); c != 0 {
		t.Fatalf("live count = %d, want 0", c)
	}
	if e, ok := r.store.Activity("act-1"); !ok || !e.Deleted || e.Version != 3 {
		t.Fatalf("tombstone = %+v ok=%v, want deleted at version 3", e, ok)
	}
}

func TestHiddenPoisonGoesToDLQAndPartitionContinues(t *testing.T) {
	r := newRig(1)
	r.log.Append("acc-1", []byte(`{"event_id":"broken"`))
	publish(r.log, ev("e2", TypeLogged, "acc-1", "act-2", 1, "after the poison"))
	stop, _ := r.start(t)
	waitFor(t, "caught up past the poison message", r.caughtUp)
	_ = stop()
	if n := len(r.dlq.Messages()); n != 1 {
		t.Fatalf("dlq has %d messages, want 1", n)
	}
	if r.store.Count("acc-1") != 1 {
		t.Fatal("the record after the poison message was not applied")
	}
}

func TestHiddenTransientFailureRetriedThenDLQ(t *testing.T) {
	r := newRig(1)
	publish(r.log, ev("bad", TypeLogged, "acc-1", "act-1", 1, "x"), ev("good", TypeLogged, "acc-1", "act-2", 1, "y"))
	var badAttempts int32
	r.store.BeforeCommit = func(_ context.Context, ids []string) error {
		for _, id := range ids {
			if id == "bad" {
				atomic.AddInt32(&badAttempts, 1)
				return store.ErrTransient
			}
		}
		return nil
	}
	stop, _ := r.start(t)
	waitFor(t, "caught up", r.caughtUp)
	_ = stop()
	if a := atomic.LoadInt32(&badAttempts); a != 3 {
		t.Fatalf("store saw %d attempts for the failing event, want 3", a)
	}
	msgs := r.dlq.Messages()
	if len(msgs) != 1 || msgs[0].Attempts != 3 || !errors.Is(store.ErrTransient, store.ErrTransient) || msgs[0].Reason == "" {
		t.Fatalf("dlq = %+v, want one message with Attempts=3 and a reason", msgs)
	}
	if r.store.Count("acc-1") != 1 || r.store.Processed("bad") {
		t.Fatalf("count=%d processed(bad)=%v: want the good event applied and the bad one not recorded", r.store.Count("acc-1"), r.store.Processed("bad"))
	}
}

func TestHiddenTransientFailureRecovers(t *testing.T) {
	r := newRig(1)
	publish(r.log, ev("e1", TypeLogged, "acc-1", "act-1", 1, "x"))
	var n int32
	r.store.BeforeCommit = func(_ context.Context, _ []string) error {
		if atomic.AddInt32(&n, 1) <= 2 {
			return store.ErrTransient
		}
		return nil
	}
	stop, _ := r.start(t)
	waitFor(t, "caught up", r.caughtUp)
	_ = stop()
	if len(r.dlq.Messages()) != 0 || r.store.Count("acc-1") != 1 {
		t.Fatalf("dlq=%d count=%d: two transient failures then success should apply once and park nothing", len(r.dlq.Messages()), r.store.Count("acc-1"))
	}
}

func TestHiddenShutdownFinishesInFlight(t *testing.T) {
	r := newRig(1)
	publish(r.log, ev("e1", TypeLogged, "acc-1", "act-1", 1, "in flight"), ev("e2", TypeLogged, "acc-1", "act-2", 1, "not started"))
	entered := make(chan struct{})
	release := make(chan struct{})
	var first sync.Once
	r.store.BeforeCommit = func(_ context.Context, ids []string) error {
		for _, id := range ids {
			if id == "e1" {
				first.Do(func() { close(entered) })
				select {
				case <-release:
				case <-time.After(3 * time.Second):
				}
			}
		}
		return nil
	}
	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan error, 1)
	go func() { done <- r.c.Run(ctx, r.log, r.group) }()
	select {
	case <-entered:
	case <-time.After(3 * time.Second):
		t.Fatal("e1 never reached the store")
	}
	cancel() // SIGTERM while e1 is mid-transaction
	close(release)
	select {
	case err := <-done:
		if err != nil {
			t.Fatalf("Run returned %v on graceful shutdown, want nil", err)
		}
	case <-time.After(3 * time.Second):
		t.Fatal("Run did not return within 3s of shutdown")
	}
	if !r.store.Processed("e1") || r.group.Committed(0) != 1 {
		t.Fatalf("in-flight e1: processed=%v committed=%d, want applied and committed (offset 1)", r.store.Processed("e1"), r.group.Committed(0))
	}
	if r.store.Processed("e2") || r.group.Committed(0) > 1 {
		t.Fatal("consumer took new work (e2) after shutdown started")
	}
}

func TestHiddenManyPartitionsWithDuplicates(t *testing.T) {
	r := newRig(4)
	want := map[string]int{}
	for a := 0; a < 12; a++ {
		acc := fmt.Sprintf("acc-%02d", a)
		for i := 0; i < 5; i++ {
			e := ev(fmt.Sprintf("%s-e%d", acc, i), TypeLogged, acc, fmt.Sprintf("%s-act%d", acc, i), 1, "s")
			publish(r.log, e)
			if i%2 == 0 {
				publish(r.log, e)
			}
		}
		del := ev(acc+"-del", TypeDeleted, acc, acc+"-act0", 2, "")
		publish(r.log, del, del)
		want[acc] = 4
	}
	stop, _ := r.start(t)
	waitFor(t, "caught up on 4 partitions", r.caughtUp)
	if err := stop(); err != nil {
		t.Fatalf("Run returned %v", err)
	}
	for acc, n := range want {
		if got := r.store.Count(acc); got != n || len(r.store.Timeline(acc)) != n {
			t.Fatalf("%s: count=%d timeline=%d, want %d", acc, got, len(r.store.Timeline(acc)), n)
		}
	}
}
