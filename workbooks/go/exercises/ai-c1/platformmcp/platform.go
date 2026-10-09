package platformmcp

import (
	"context"
	"errors"
	"fmt"
	"sort"
	"sync"
	"time"
)

// Deployment is the read model the tools expose.
type Deployment struct {
	Namespace string `json:"namespace"`
	Name      string `json:"name"`
	Image     string `json:"image"`
	Replicas  int    `json:"replicas"`
	Ready     int    `json:"ready"`
}

// Rollout is the status of the latest rollout of a Deployment.
type Rollout struct {
	Namespace string `json:"namespace"`
	Name      string `json:"name"`
	Revision  int    `json:"revision"`
	Status    string `json:"status"` // Complete, Progressing, Failed
	Message   string `json:"message"`
}

// ErrNotFound is returned by Platform methods for unknown deployments.
var ErrNotFound = errors.New("deployment not found")

// Platform is what the MCP tools call. In production it is backed by client-go;
// here it is an in-memory fake. You do not need to change this file.
type Platform interface {
	ListDeployments(ctx context.Context, namespace string) ([]Deployment, error)
	RolloutStatus(ctx context.Context, namespace, name string) (Rollout, error)
	// Restart triggers a rolling restart. actor is the authenticated subject,
	// recorded for the audit log.
	Restart(ctx context.Context, namespace, name, actor, reason string) error
}

// RestartRecord is one audited restart.
type RestartRecord struct {
	Namespace, Name, Actor, Reason string
	At                             time.Time
}

// FakePlatform is an in-memory Platform with a few deployments.
type FakePlatform struct {
	mu       sync.Mutex
	deps     map[string]Deployment
	rollouts map[string]Rollout
	Restarts []RestartRecord
}

// NewFakePlatform returns a platform with checkout, cart and coredns.
func NewFakePlatform() *FakePlatform {
	f := &FakePlatform{deps: map[string]Deployment{}, rollouts: map[string]Rollout{}}
	for _, d := range []Deployment{
		{"shop", "checkout", "registry.kestrel.dev/checkout:2.14.1", 6, 2},
		{"shop", "cart", "registry.kestrel.dev/cart:1.9.0", 3, 3},
		{"kube-system", "coredns", "coredns/coredns:1.12.0", 2, 2},
	} {
		f.deps[d.Namespace+"/"+d.Name] = d
	}
	f.rollouts["shop/checkout"] = Rollout{"shop", "checkout", 41, "Progressing", "4 of 6 updated replicas are unavailable: CrashLoopBackOff"}
	f.rollouts["shop/cart"] = Rollout{"shop", "cart", 17, "Complete", "successfully rolled out"}
	f.rollouts["kube-system/coredns"] = Rollout{"kube-system", "coredns", 3, "Complete", "successfully rolled out"}
	return f
}

func (f *FakePlatform) ListDeployments(ctx context.Context, namespace string) ([]Deployment, error) {
	f.mu.Lock()
	defer f.mu.Unlock()
	var out []Deployment
	for _, d := range f.deps {
		if d.Namespace == namespace {
			out = append(out, d)
		}
	}
	sort.Slice(out, func(i, j int) bool { return out[i].Name < out[j].Name })
	return out, nil
}

func (f *FakePlatform) RolloutStatus(ctx context.Context, namespace, name string) (Rollout, error) {
	f.mu.Lock()
	defer f.mu.Unlock()
	r, ok := f.rollouts[namespace+"/"+name]
	if !ok {
		return Rollout{}, fmt.Errorf("%s/%s: %w", namespace, name, ErrNotFound)
	}
	return r, nil
}

func (f *FakePlatform) Restart(ctx context.Context, namespace, name, actor, reason string) error {
	f.mu.Lock()
	defer f.mu.Unlock()
	if _, ok := f.deps[namespace+"/"+name]; !ok {
		return fmt.Errorf("%s/%s: %w", namespace, name, ErrNotFound)
	}
	f.Restarts = append(f.Restarts, RestartRecord{namespace, name, actor, reason, time.Now()})
	return nil
}

// RestartCount returns the number of recorded restarts (safe for concurrent use).
func (f *FakePlatform) RestartCount() int {
	f.mu.Lock()
	defer f.mu.Unlock()
	return len(f.Restarts)
}

// LastRestart returns the most recent restart record.
func (f *FakePlatform) LastRestart() (RestartRecord, bool) {
	f.mu.Lock()
	defer f.mu.Unlock()
	if len(f.Restarts) == 0 {
		return RestartRecord{}, false
	}
	return f.Restarts[len(f.Restarts)-1], true
}
