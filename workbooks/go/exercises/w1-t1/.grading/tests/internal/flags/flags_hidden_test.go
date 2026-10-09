package flags

import (
	"context"
	"errors"
	"fmt"
	"reflect"
	"testing"
	"time"
)

func svc() *Service {
	return &Service{Store: NewMemStore(), Now: func() time.Time { return time.Date(2026, 10, 6, 14, 0, 0, 0, time.UTC) }}
}

func validFlag() Flag {
	return Flag{Key: "checkout-v2", Owner: "payments@corvidpay.example", Env: "prod", Enabled: true, Rollout: 10}
}

func TestHiddenServicePutValidReturnsUntypedNil(t *testing.T) {
	err := svc().Put(context.Background(), validFlag())
	if err != nil {
		t.Fatalf("Put(valid) = %v (dynamic type %T); want a nil error interface", err, err)
	}
}

func TestHiddenServicePutValidPersists(t *testing.T) {
	s := svc()
	if err := s.Put(context.Background(), validFlag()); err != nil {
		t.Fatalf("Put: %v", err)
	}
	got, err := s.Get(context.Background(), "checkout-v2")
	if err != nil {
		t.Fatalf("Get after Put: %v", err)
	}
	if got.UpdatedAt.IsZero() || got.Rollout != 10 || got.Owner != "payments@corvidpay.example" {
		t.Fatalf("stored flag = %+v", got)
	}
}

func TestHiddenInvalidFlagErrorsAsValidationErrorWithAllFields(t *testing.T) {
	f := Flag{Key: "Bad_Key", Owner: "growth", Env: "qa", Rollout: 120}
	err := svc().Put(context.Background(), f)
	if err == nil {
		t.Fatal("Put(invalid) returned nil")
	}
	wrapped := fmt.Errorf("handler: %w", err)
	var verr *ValidationError
	if !errors.As(wrapped, &verr) || verr == nil {
		t.Fatalf("errors.As did not find a non-nil *ValidationError in %v", wrapped)
	}
	want := []string{"env", "key", "owner", "rollout"}
	for _, k := range want {
		if _, ok := verr.Fields[k]; !ok {
			t.Fatalf("Fields = %v; missing %q (all invalid fields must be reported at once)", verr.Fields, k)
		}
	}
}

func TestHiddenEnabledZeroRolloutRejected(t *testing.T) {
	f := validFlag()
	f.Rollout = 0
	var verr *ValidationError
	if err := svc().Put(context.Background(), f); !errors.As(err, &verr) || verr.FieldErrors()["rollout"] == "" {
		t.Fatalf("enabled flag with 0%% rollout must fail validation on rollout; got %v", err)
	}
	f.Enabled = false
	if err := svc().Put(context.Background(), f); err != nil {
		t.Fatalf("disabled flag with 0%% rollout is valid; got %v", err)
	}
}

func TestHiddenValidationErrorMessageStable(t *testing.T) {
	e := &ValidationError{Fields: map[string]string{"rollout": "r", "key": "k"}}
	if got := e.Error(); got != "invalid flag: key: k; rollout: r" {
		t.Fatalf("Error() = %q", got)
	}
	var nilErr *ValidationError
	if nilErr.FieldErrors() != nil {
		t.Fatal("FieldErrors on nil receiver must return nil")
	}
}

func TestHiddenDescriptionStillOmittedWhenEmpty(t *testing.T) {
	// The omitempty change in PLAT-2291 was intended; the fix must not revert it.
	field, _ := reflect.TypeOf(Flag{}).FieldByName("Description")
	if field.Tag.Get("json") != "description,omitempty" {
		t.Fatalf("Description json tag = %q; the omitempty change was a red herring, keep it", field.Tag.Get("json"))
	}
}
