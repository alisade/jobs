package fn

import (
	"context"
	"testing"
)

func riqXR() XR {
	return XR{
		APIVersion: XRAPIVersion, Kind: XRKind,
		Metadata: ObjectMeta{Name: "riq-scores", Namespace: "team-riq"},
		Spec:     XRSpec{Size: "medium", Version: "postgres-16", Team: "riq"},
	}
}

func byKey(rs []Resource) map[string]Resource {
	m := map[string]Resource{}
	for _, r := range rs {
		m[r.Key()] = r
	}
	return m
}

func TestComposeMediumHappyPath(t *testing.T) {
	res := Compose(riqXR())
	if res.Fatal != "" {
		t.Fatalf("unexpected fatal: %s", res.Fatal)
	}
	if len(res.Desired) != 3 {
		t.Fatalf("want 3 composed resources (instance, database, user), got %d", len(res.Desired))
	}
	m := byKey(res.Desired)
	inst, ok := m["DatabaseInstance/riq-scores-pg"]
	if !ok {
		t.Fatalf("missing DatabaseInstance/riq-scores-pg, have %v", keys(res.Desired))
	}
	if inst.ForProvider["tier"] != "db-custom-2-7680" || inst.ForProvider["databaseVersion"] != "POSTGRES_16" {
		t.Errorf("instance forProvider = %v", inst.ForProvider)
	}
	if inst.ForProvider["region"] != DefaultRegion {
		t.Errorf("region = %q, want default %q", inst.ForProvider["region"], DefaultRegion)
	}
	for _, r := range res.Desired {
		if r.APIVersion != MRAPIVersion || r.Metadata.Namespace != "team-riq" {
			t.Errorf("%s: apiVersion %q namespace %q", r.Key(), r.APIVersion, r.Metadata.Namespace)
		}
		if r.Metadata.Labels[LabelComposite] != "riq-scores" || r.Metadata.Labels[LabelTeam] != "riq" {
			t.Errorf("%s: labels %v", r.Key(), r.Metadata.Labels)
		}
		if r.ProviderConfigRef != (ProviderConfigRef{Kind: "ClusterProviderConfig", Name: "default"}) {
			t.Errorf("%s: providerConfigRef %v", r.Key(), r.ProviderConfigRef)
		}
		if r.DeletionPolicy != "Delete" {
			t.Errorf("%s: deletionPolicy %q, want default Delete", r.Key(), r.DeletionPolicy)
		}
	}
	u := m["User/riq-scores-user"]
	if u.WriteConnectionSecretToRef == nil || u.WriteConnectionSecretToRef.Name != "riq-scores-conn" {
		t.Errorf("user connection secret = %v", u.WriteConnectionSecretToRef)
	}
	if u.ForProvider["instance"] != "riq-scores-pg" || m["Database/riq-scores-db"].ForProvider["instance"] != "riq-scores-pg" {
		t.Errorf("database and user must reference the instance riq-scores-pg")
	}
}

func TestReconcileCreatesThenBecomesReady(t *testing.T) {
	ctx := context.Background()
	c := NewFakeClient()
	xr, err := Reconcile(ctx, c, riqXR())
	if err != nil {
		t.Fatalf("reconcile: %v", err)
	}
	if n := len(c.All()); n != 3 {
		t.Fatalf("want 3 stored resources after first reconcile, got %d", n)
	}
	if got := FindCondition(xr.Conditions, "Ready"); got.Status != "False" {
		t.Fatalf("freshly created resources are not Ready yet; Ready=%+v", got)
	}
	for _, r := range c.All() {
		c.SetReady(r.Metadata.Namespace, r.Kind, r.Metadata.Name, true)
	}
	xr, err = Reconcile(ctx, c, xr)
	if err != nil {
		t.Fatalf("reconcile 2: %v", err)
	}
	if got := FindCondition(xr.Conditions, "Ready"); got.Status != "True" {
		t.Fatalf("all composed resources are Ready; want XR Ready=True, got %+v", got)
	}
	if got := FindCondition(xr.Conditions, "Synced"); got.Status != "True" {
		t.Fatalf("want Synced=True, got %+v", got)
	}
}

func keys(rs []Resource) []string {
	var out []string
	for _, r := range rs {
		out = append(out, r.Key())
	}
	return out
}
