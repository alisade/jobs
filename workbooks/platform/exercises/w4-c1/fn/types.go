// Package fn is a small, local stand-in for a Crossplane v2 composition function plus the
// composite reconciler that drives it. It models only what this exercise needs.
//
// Crossplane v2 vocabulary used here:
//   - AppDatabase is a namespaced composite resource (XR). There are no claims in v2 for new
//     APIs; developers create the XR directly in their team namespace.
//   - The composed resources are namespaced managed resources (MRs) from the Upbound GCP
//     provider family, API group sql.gcp.m.upbound.io (the ".m." groups are the namespaced ones).
//   - Every composed MR carries the label crossplane.io/composite=<xr name>; that is how the
//     reconciler finds what it composed earlier.
package fn

import (
	"context"
	"maps"
	"reflect"
)

// You should not need to change this file. Write your code in compose.go and reconcile.go.

const (
	XRAPIVersion = "platform.tessellate.example/v1alpha1"
	XRKind       = "AppDatabase"
	MRAPIVersion = "sql.gcp.m.upbound.io/v1beta1"

	KindInstance = "DatabaseInstance"
	KindDatabase = "Database"
	KindUser     = "User"

	LabelComposite = "crossplane.io/composite"
	LabelTeam      = "platform.tessellate.example/team"

	DefaultRegion = "us-central1"
)

// ObjectMeta is the subset of Kubernetes object metadata the exercise uses.
type ObjectMeta struct {
	Name      string
	Namespace string
	Labels    map[string]string
}

// ProviderConfigRef selects the credentials a managed resource uses. In Crossplane v2 a
// namespaced MR can reference a namespaced ProviderConfig (looked up in the MR's own
// namespace) or a cluster-scoped ClusterProviderConfig.
type ProviderConfigRef struct {
	Kind string
	Name string
}

// SecretRef names a connection secret. For namespaced MRs the secret is always written to the
// MR's own namespace, so there is no namespace field.
type SecretRef struct {
	Name string
}

// Condition is a status condition (Synced, Ready).
type Condition struct {
	Type    string // "Synced" or "Ready"
	Status  string // "True" or "False"
	Reason  string
	Message string
}

// XRSpec is what a developer writes in their AppDatabase.
type XRSpec struct {
	Size              string             // small | medium | large
	Version           string             // postgres-15 | postgres-16
	Team              string             // owning team, lower-case DNS label, e.g. "riq"
	Region            string             // optional, default us-central1
	DeletionPolicy    string             // optional: "" (means Delete), "Delete" or "Orphan"
	ProviderConfigRef *ProviderConfigRef // optional override of the platform default
}

// XR is a namespaced AppDatabase composite resource.
type XR struct {
	APIVersion string
	Kind       string
	Metadata   ObjectMeta
	Spec       XRSpec
	Conditions []Condition
}

// Resource is a composed managed resource. ForProvider holds the provider fields as strings to
// keep the model small. Conditions are written by the provider (here: the fake client), never
// by the composition function.
type Resource struct {
	APIVersion                 string
	Kind                       string
	Metadata                   ObjectMeta
	ForProvider                map[string]string
	DeletionPolicy             string
	ProviderConfigRef          ProviderConfigRef
	WriteConnectionSecretToRef *SecretRef
	Conditions                 []Condition
}

// Key identifies a resource inside one namespace.
func (r Resource) Key() string { return r.Kind + "/" + r.Metadata.Name }

// SameDesired reports whether two resources have the same desired state. Status conditions
// are ignored because the provider owns them.
func SameDesired(a, b Resource) bool {
	if a.APIVersion != b.APIVersion || a.Kind != b.Kind || a.DeletionPolicy != b.DeletionPolicy {
		return false
	}
	if a.Metadata.Name != b.Metadata.Name || a.Metadata.Namespace != b.Metadata.Namespace {
		return false
	}
	if !maps.Equal(a.Metadata.Labels, b.Metadata.Labels) || !maps.Equal(a.ForProvider, b.ForProvider) {
		return false
	}
	if a.ProviderConfigRef != b.ProviderConfigRef {
		return false
	}
	return reflect.DeepEqual(a.WriteConnectionSecretToRef, b.WriteConnectionSecretToRef)
}

// IsReady reports whether a resource has condition Ready=True.
func IsReady(r Resource) bool {
	return FindCondition(r.Conditions, "Ready").Status == "True"
}

// FindCondition returns the condition of the given type, or a zero Condition.
func FindCondition(cs []Condition, t string) Condition {
	for _, c := range cs {
		if c.Type == t {
			return c
		}
	}
	return Condition{}
}

// SetCondition replaces (or appends) the condition with the same Type.
func SetCondition(cs []Condition, c Condition) []Condition {
	out := make([]Condition, 0, len(cs)+1)
	done := false
	for _, x := range cs {
		if x.Type == c.Type {
			out = append(out, c)
			done = true
			continue
		}
		out = append(out, x)
	}
	if !done {
		out = append(out, c)
	}
	return out
}

// Result is what the composition function returns: either the desired composed resources, or
// a Fatal message explaining why the XR cannot be composed (bad input). Never both.
type Result struct {
	Desired []Resource
	Fatal   string
}

// Client is the slice of the Kubernetes API the reconciler needs.
type Client interface {
	// List returns the managed resources in namespace whose labels contain every key/value in
	// selector. An empty namespace means all namespaces.
	List(ctx context.Context, namespace string, selector map[string]string) ([]Resource, error)
	// Apply creates or replaces the desired state of a resource (server-side apply). Status
	// conditions in r are ignored; the stored conditions are kept.
	Apply(ctx context.Context, r Resource) error
	// Delete removes a resource.
	Delete(ctx context.Context, namespace, kind, name string) error
	// UpdateXRStatus writes the XR's conditions.
	UpdateXRStatus(ctx context.Context, xr XR) error
}
