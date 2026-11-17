package consumer

import (
	"encoding/json"
	"errors"
	"fmt"
	"time"
)

// Event types on the activity topic (published by accounts-svc and pipeline-svc via the outbox).
const (
	TypeLogged  = "ActivityLogged"
	TypeEdited  = "ActivityEdited"
	TypeDeleted = "ActivityDeleted"
)

// Event is the decoded envelope. Version is the activity's version after the change: Logged is
// version 1, every edit or delete increments it. event_id is stable across producer retries and
// relay redeliveries (it is the outbox row id).
type Event struct {
	EventID    string    `json:"event_id"`
	Type       string    `json:"type"`
	AccountID  string    `json:"account_id"`
	ActivityID string    `json:"activity_id"`
	Version    int       `json:"version"`
	Subject    string    `json:"subject,omitempty"`
	OccurredAt time.Time `json:"occurred_at"`
}

// ErrPoison marks a message that can never be applied (bad JSON, unknown type, missing fields).
// Retrying it is pointless.
var ErrPoison = errors.New("poison message")

// Decode parses and validates one record value. Errors wrap ErrPoison.
func Decode(b []byte) (Event, error) {
	var e Event
	if err := json.Unmarshal(b, &e); err != nil {
		return e, fmt.Errorf("%w: %v", ErrPoison, err)
	}
	switch e.Type {
	case TypeLogged, TypeEdited, TypeDeleted:
	default:
		return e, fmt.Errorf("%w: unknown type %q", ErrPoison, e.Type)
	}
	if e.EventID == "" || e.AccountID == "" || e.ActivityID == "" || e.Version < 1 {
		return e, fmt.Errorf("%w: missing event_id, account_id, activity_id or version", ErrPoison)
	}
	return e, nil
}

// Encode is the producer side, used by tests and cmd/replay.
func Encode(e Event) []byte {
	b, _ := json.Marshal(e)
	return b
}
