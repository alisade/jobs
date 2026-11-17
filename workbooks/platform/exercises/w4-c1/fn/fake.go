package fn

import (
	"context"
	"fmt"
	"sort"
	"sync"
)

// FakeClient is an in-memory Client for tests. It counts writes so tests can check that a
// second reconcile of an unchanged XR is a no-op. You should not need to change it.
type FakeClient struct {
	mu        sync.Mutex
	objs      map[string]Resource // key: namespace/kind/name
	Applies   int
	Deletes   int
	StatusOps int
	LastXR    XR
	// FailApply, when set, makes Apply return this error.
	FailApply error
}

func NewFakeClient(seed ...Resource) *FakeClient {
	f := &FakeClient{objs: map[string]Resource{}}
	for _, r := range seed {
		f.objs[fkey(r.Metadata.Namespace, r.Kind, r.Metadata.Name)] = r
	}
	return f
}

func fkey(ns, kind, name string) string { return ns + "/" + kind + "/" + name }

// Writes is the number of Apply and Delete calls that reached the API.
func (f *FakeClient) Writes() int { f.mu.Lock(); defer f.mu.Unlock(); return f.Applies + f.Deletes }

func (f *FakeClient) List(_ context.Context, namespace string, selector map[string]string) ([]Resource, error) {
	f.mu.Lock()
	defer f.mu.Unlock()
	var out []Resource
	for _, r := range f.objs {
		if namespace != "" && r.Metadata.Namespace != namespace {
			continue
		}
		ok := true
		for k, v := range selector {
			if r.Metadata.Labels[k] != v {
				ok = false
				break
			}
		}
		if ok {
			out = append(out, r)
		}
	}
	sort.Slice(out, func(i, j int) bool {
		return fkey(out[i].Metadata.Namespace, out[i].Kind, out[i].Metadata.Name) <
			fkey(out[j].Metadata.Namespace, out[j].Kind, out[j].Metadata.Name)
	})
	return out, nil
}

func (f *FakeClient) Apply(_ context.Context, r Resource) error {
	f.mu.Lock()
	defer f.mu.Unlock()
	if f.FailApply != nil {
		return f.FailApply
	}
	if r.Metadata.Namespace == "" {
		return fmt.Errorf("apply %s: namespaced managed resources need a namespace", r.Key())
	}
	k := fkey(r.Metadata.Namespace, r.Kind, r.Metadata.Name)
	if old, ok := f.objs[k]; ok {
		r.Conditions = old.Conditions
	} else {
		r.Conditions = []Condition{{Type: "Ready", Status: "False", Reason: "Creating"}}
	}
	f.objs[k] = r
	f.Applies++
	return nil
}

func (f *FakeClient) Delete(_ context.Context, namespace, kind, name string) error {
	f.mu.Lock()
	defer f.mu.Unlock()
	k := fkey(namespace, kind, name)
	if _, ok := f.objs[k]; !ok {
		return fmt.Errorf("delete %s: not found", k)
	}
	delete(f.objs, k)
	f.Deletes++
	return nil
}

func (f *FakeClient) UpdateXRStatus(_ context.Context, xr XR) error {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.StatusOps++
	f.LastXR = xr
	return nil
}

// Get returns a stored resource.
func (f *FakeClient) Get(namespace, kind, name string) (Resource, bool) {
	f.mu.Lock()
	defer f.mu.Unlock()
	r, ok := f.objs[fkey(namespace, kind, name)]
	return r, ok
}

// SetReady plays the provider: it marks a stored resource Ready (or not).
func (f *FakeClient) SetReady(namespace, kind, name string, ready bool) {
	f.mu.Lock()
	defer f.mu.Unlock()
	k := fkey(namespace, kind, name)
	r, ok := f.objs[k]
	if !ok {
		return
	}
	c := Condition{Type: "Ready", Status: "False", Reason: "Creating"}
	if ready {
		c = Condition{Type: "Ready", Status: "True", Reason: "Available"}
	}
	r.Conditions = SetCondition(r.Conditions, c)
	f.objs[k] = r
}

// All returns every stored resource.
func (f *FakeClient) All() []Resource { out, _ := f.List(context.Background(), "", nil); return out }
