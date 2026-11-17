package consumer

import (
	"errors"
	"testing"
)

func TestDecodeRejectsPoison(t *testing.T) {
	for _, raw := range []string{"not json", `{"type":"Nope","event_id":"e","account_id":"a","activity_id":"x","version":1}`, `{"type":"ActivityLogged"}`} {
		if _, err := Decode([]byte(raw)); !errors.Is(err, ErrPoison) {
			t.Errorf("Decode(%q) err = %v, want ErrPoison", raw, err)
		}
	}
}

func TestHappyPathBuildsTimeline(t *testing.T) {
	r := newRig(2)
	publish(r.log,
		ev("e1", TypeLogged, "acc-1", "act-1", 1, "Discovery call"),
		ev("e2", TypeLogged, "acc-1", "act-2", 1, "Sent pricing"),
		ev("e3", TypeLogged, "acc-2", "act-3", 1, "Intro email"),
	)
	stop, _ := r.start(t)
	waitFor(t, "all partitions committed", r.caughtUp)
	if err := stop(); err != nil {
		t.Fatalf("Run returned %v on clean shutdown, want nil", err)
	}
	if got := r.store.Timeline("acc-1"); len(got) != 2 {
		t.Fatalf("acc-1 timeline = %s, want 2 entries", subjects(got))
	}
	if r.store.Count("acc-1") != 2 || r.store.Count("acc-2") != 1 {
		t.Fatalf("counts acc-1=%d acc-2=%d, want 2 and 1", r.store.Count("acc-1"), r.store.Count("acc-2"))
	}
}
