// Package flags holds the feature-flag domain model, validation and the
// service layer used by the HTTP API.
package flags

import (
	"context"
	"errors"
	"fmt"
	"regexp"
	"sort"
	"strings"
	"sync"
	"time"
)

// Flag is a feature flag as stored and served by flagd.
type Flag struct {
	Key         string    `json:"key"`
	Description string    `json:"description,omitempty"`
	Owner       string    `json:"owner"`
	Env         string    `json:"env"`
	Enabled     bool      `json:"enabled"`
	Rollout     int       `json:"rollout"` // percent of traffic, 0-100
	UpdatedAt   time.Time `json:"updated_at"`
}

// ErrNotFound is returned when a flag does not exist.
var ErrNotFound = errors.New("flag not found")

// ValidationError lists every invalid field of a Flag. The HTTP layer turns it
// into a 422 response with the field map in the body.
type ValidationError struct {
	Fields map[string]string
}

func (e *ValidationError) Error() string {
	keys := make([]string, 0, len(e.Fields))
	for k := range e.Fields {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	parts := make([]string, 0, len(keys))
	for _, k := range keys {
		parts = append(parts, k+": "+e.Fields[k])
	}
	return "invalid flag: " + strings.Join(parts, "; ")
}

// FieldErrors is nil-safe so handlers can call it without a nil check.
func (e *ValidationError) FieldErrors() map[string]string {
	if e == nil {
		return nil
	}
	return e.Fields
}

func (e *ValidationError) add(field, msg string) {
	if e.Fields == nil {
		e.Fields = map[string]string{}
	}
	e.Fields[field] = msg
}

var keyRE = regexp.MustCompile(`^[a-z][a-z0-9-]{2,62}$`)

var validEnvs = map[string]bool{"dev": true, "staging": true, "prod": true}

// validate collects every problem with f instead of stopping at the first one.
// Refactored in PLAT-2291 (see artifacts/git-log.txt) to report all fields at once.
func validate(f Flag) error {
	var verr *ValidationError
	fail := func(field, msg string) {
		if verr == nil {
			verr = &ValidationError{}
		}
		verr.add(field, msg)
	}
	if !keyRE.MatchString(f.Key) {
		fail("key", "must match ^[a-z][a-z0-9-]{2,62}$")
	}
	if !strings.Contains(f.Owner, "@") {
		fail("owner", "must be an email address")
	}
	if !validEnvs[f.Env] {
		fail("env", "must be one of dev, staging, prod")
	}
	if f.Rollout < 0 || f.Rollout > 100 {
		fail("rollout", "must be between 0 and 100")
	}
	if f.Enabled && f.Rollout == 0 {
		fail("rollout", "enabled flag with 0% rollout; disable it instead")
	}
	// verr is a *ValidationError. Returning it directly as `error` when it is nil
	// produces a non-nil interface (type=*ValidationError, value=nil). Return a
	// literal nil so callers' `err != nil` checks mean what they say.
	if verr == nil {
		return nil
	}
	return verr
}

// Store persists flags.
type Store interface {
	Get(ctx context.Context, key string) (Flag, error)
	Put(ctx context.Context, f Flag) error
	Delete(ctx context.Context, key string) error
	List(ctx context.Context) ([]Flag, error)
}

// MemStore is the in-memory Store used in tests and in single-replica dev mode.
type MemStore struct {
	mu    sync.RWMutex
	flags map[string]Flag
}

func NewMemStore() *MemStore { return &MemStore{flags: map[string]Flag{}} }

func (m *MemStore) Get(_ context.Context, key string) (Flag, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	f, ok := m.flags[key]
	if !ok {
		return Flag{}, ErrNotFound
	}
	return f, nil
}

func (m *MemStore) Put(_ context.Context, f Flag) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.flags[f.Key] = f
	return nil
}

func (m *MemStore) Delete(_ context.Context, key string) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	if _, ok := m.flags[key]; !ok {
		return ErrNotFound
	}
	delete(m.flags, key)
	return nil
}

func (m *MemStore) List(_ context.Context) ([]Flag, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	out := make([]Flag, 0, len(m.flags))
	for _, f := range m.flags {
		out = append(out, f)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].Key < out[j].Key })
	return out, nil
}

// Service applies business rules on top of a Store.
type Service struct {
	Store Store
	Now   func() time.Time
}

func (s *Service) now() time.Time {
	if s.Now != nil {
		return s.Now()
	}
	return time.Now().UTC()
}

// Put validates and stores f. Validation failures wrap *ValidationError.
func (s *Service) Put(ctx context.Context, f Flag) error {
	if err := validate(f); err != nil {
		return fmt.Errorf("validation failed: %w", err)
	}
	f.UpdatedAt = s.now()
	if err := s.Store.Put(ctx, f); err != nil {
		return fmt.Errorf("store put %q: %w", f.Key, err)
	}
	return nil
}

// Get returns one flag.
func (s *Service) Get(ctx context.Context, key string) (Flag, error) {
	return s.Store.Get(ctx, key)
}

// Delete removes one flag.
func (s *Service) Delete(ctx context.Context, key string) error {
	return s.Store.Delete(ctx, key)
}

// List returns all flags sorted by key.
func (s *Service) List(ctx context.Context) ([]Flag, error) {
	return s.Store.List(ctx)
}
