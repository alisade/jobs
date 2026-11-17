package fn

import (
	"context"
	"errors"
	"strings"
	"testing"
)

func hxr(size string) XR {
	x := riqXR()
	x.Spec.Size = size
	return x
}

func readyAll(c *FakeClient) {
	for _, r := range c.All() {
		c.SetReady(r.Metadata.Namespace, r.Kind, r.Metadata.Name, true)
	}
}

func TestHiddenInvalidInputIsFatalNotPanic(t *testing.T) {
	cases := map[string]func(*XR){
		"spec.size":                   func(x *XR) { x.Spec.Size = "xl" },
		"spec.version":                func(x *XR) { x.Spec.Version = "mysql-8" },
		"spec.team":                   func(x *XR) { x.Spec.Team = "" },
		"spec.deletionPolicy":         func(x *XR) { x.Spec.DeletionPolicy = "Keep" },
		"metadata.namespace":          func(x *XR) { x.Metadata.Namespace = "" },
		"spec.providerConfigRef.name": func(x *XR) { x.Spec.ProviderConfigRef = &ProviderConfigRef{Kind: "ProviderConfig"} },
	}
	for field, mut := range cases {
		x := riqXR()
		mut(&x)
		var res Result
		func() {
			defer func() {
				if r := recover(); r != nil {
					t.Errorf("%s: Compose panicked: %v", field, r)
				}
			}()
			res = Compose(x)
		}()
		if res.Fatal == "" || len(res.Desired) != 0 {
			t.Errorf("%s: want Fatal and no resources, got fatal=%q n=%d", field, res.Fatal, len(res.Desired))
			continue
		}
		if !strings.Contains(res.Fatal, field) {
			t.Errorf("fatal message should name the field %q: %q", field, res.Fatal)
		}
	}
}

func TestHiddenFatalSetsConditionsAndWritesNothing(t *testing.T) {
	c := NewFakeClient()
	x := hxr("xl")
	out, err := Reconcile(context.Background(), c, x)
	if err != nil {
		t.Fatalf("bad input is a condition, not a reconcile error: %v", err)
	}
	if c.Writes() != 0 {
		t.Fatalf("fatal compose must not write managed resources, writes=%d", c.Writes())
	}
	s := FindCondition(out.Conditions, "Synced")
	if s.Status != "False" || s.Reason != "ComposeFailed" || !strings.Contains(s.Message, "spec.size") {
		t.Fatalf("Synced = %+v", s)
	}
	if FindCondition(out.Conditions, "Ready").Status != "False" {
		t.Fatalf("Ready must be False on a fatal result")
	}
	if c.StatusOps == 0 {
		t.Fatalf("the XR status must be written so the developer sees the message")
	}
}

func TestHiddenProviderConfigOverride(t *testing.T) {
	x := riqXR()
	x.Spec.ProviderConfigRef = &ProviderConfigRef{Kind: "ProviderConfig", Name: "riq-sandbox"}
	res := Compose(x)
	if res.Fatal != "" {
		t.Fatal(res.Fatal)
	}
	for _, r := range res.Desired {
		if r.ProviderConfigRef != (ProviderConfigRef{Kind: "ProviderConfig", Name: "riq-sandbox"}) {
			t.Errorf("%s: providerConfigRef %v, want the XR override", r.Key(), r.ProviderConfigRef)
		}
	}
	x.Spec.ProviderConfigRef = &ProviderConfigRef{Name: "shared-ci"}
	for _, r := range Compose(x).Desired {
		if r.ProviderConfigRef != (ProviderConfigRef{Kind: "ClusterProviderConfig", Name: "shared-ci"}) {
			t.Errorf("override without kind should default to ClusterProviderConfig: %v", r.ProviderConfigRef)
		}
	}
}

func TestHiddenLargeAddsReplicaAndRegional(t *testing.T) {
	res := Compose(hxr("large"))
	got := keys(res.Desired)
	want := []string{"DatabaseInstance/riq-scores-pg", "DatabaseInstance/riq-scores-pg-replica", "Database/riq-scores-db", "User/riq-scores-user"}
	if strings.Join(got, ",") != strings.Join(want, ",") {
		t.Fatalf("large composes %v, want %v (in that order)", got, want)
	}
	m := byKey(res.Desired)
	if m["DatabaseInstance/riq-scores-pg"].ForProvider["availabilityType"] != "REGIONAL" {
		t.Errorf("large primary must be REGIONAL")
	}
	if m["DatabaseInstance/riq-scores-pg-replica"].ForProvider["masterInstanceName"] != "riq-scores-pg" {
		t.Errorf("replica must point at the primary")
	}
	if Compose(hxr("small")).Desired[0].ForProvider["availabilityType"] != "ZONAL" {
		t.Errorf("small must be ZONAL")
	}
}

func TestHiddenDeletionPolicyAndRegionPropagate(t *testing.T) {
	x := riqXR()
	x.Spec.DeletionPolicy = "Orphan"
	x.Spec.Region = "us-east4"
	res := Compose(x)
	for _, r := range res.Desired {
		if r.DeletionPolicy != "Orphan" {
			t.Errorf("%s deletionPolicy %q", r.Key(), r.DeletionPolicy)
		}
	}
	if res.Desired[0].ForProvider["region"] != "us-east4" {
		t.Errorf("region override lost")
	}
	if len(res.Desired[0].Metadata.Labels) != 2 {
		t.Errorf("composed labels must be exactly composite + team: %v", res.Desired[0].Metadata.Labels)
	}
}

func TestHiddenNoClaimsComposed(t *testing.T) {
	for _, r := range Compose(hxr("large")).Desired {
		if strings.Contains(r.Kind, "Claim") || r.APIVersion != MRAPIVersion {
			t.Errorf("v2 composes namespaced MRs directly, got %s %s", r.APIVersion, r.Kind)
		}
	}
}

func TestHiddenSecondReconcileIsNoOp(t *testing.T) {
	ctx := context.Background()
	c := NewFakeClient()
	x, err := Reconcile(ctx, c, riqXR())
	if err != nil {
		t.Fatal(err)
	}
	readyAll(c)
	before := c.Writes()
	if _, err := Reconcile(ctx, c, x); err != nil {
		t.Fatal(err)
	}
	if _, err := Reconcile(ctx, c, x); err != nil {
		t.Fatal(err)
	}
	if c.Writes() != before {
		t.Fatalf("unchanged XR must not re-apply: writes %d -> %d", before, c.Writes())
	}
}

func TestHiddenSpecChangeReappliesOnlyChanged(t *testing.T) {
	ctx := context.Background()
	c := NewFakeClient()
	x, _ := Reconcile(ctx, c, riqXR())
	before := c.Applies
	x.Spec.Version = "postgres-15"
	if _, err := Reconcile(ctx, c, x); err != nil {
		t.Fatal(err)
	}
	if c.Applies-before != 1 {
		t.Fatalf("a version change touches only the instance; applies +%d", c.Applies-before)
	}
	r, _ := c.Get("team-riq", KindInstance, "riq-scores-pg")
	if r.ForProvider["databaseVersion"] != "POSTGRES_15" {
		t.Fatalf("instance not updated: %v", r.ForProvider)
	}
}

func TestHiddenReadyMessageNamesNotReady(t *testing.T) {
	ctx := context.Background()
	c := NewFakeClient()
	x, _ := Reconcile(ctx, c, riqXR())
	c.SetReady("team-riq", KindInstance, "riq-scores-pg", true)
	x, _ = Reconcile(ctx, c, x)
	rd := FindCondition(x.Conditions, "Ready")
	if rd.Status != "False" || rd.Reason != "Creating" {
		t.Fatalf("Ready = %+v", rd)
	}
	if rd.Message != "waiting for: Database/riq-scores-db, User/riq-scores-user" {
		t.Fatalf("message = %q", rd.Message)
	}
}

func TestHiddenDownsizeRemovesReplica(t *testing.T) {
	ctx := context.Background()
	c := NewFakeClient()
	x, _ := Reconcile(ctx, c, hxr("large"))
	if _, ok := c.Get("team-riq", KindInstance, "riq-scores-pg-replica"); !ok {
		t.Fatalf("large should create the replica")
	}
	x.Spec.Size = "medium"
	if _, err := Reconcile(ctx, c, x); err != nil {
		t.Fatal(err)
	}
	if _, ok := c.Get("team-riq", KindInstance, "riq-scores-pg-replica"); ok {
		t.Fatalf("replica no longer desired and must be deleted")
	}
	if len(c.All()) != 3 {
		t.Fatalf("want 3 resources after downsize, have %d", len(c.All()))
	}
}

func TestHiddenNamespaceScoping(t *testing.T) {
	ctx := context.Background()
	other := Resource{APIVersion: MRAPIVersion, Kind: KindInstance,
		Metadata: ObjectMeta{Name: "riq-scores-pg-old", Namespace: "team-mdm",
			Labels: map[string]string{LabelComposite: "riq-scores", LabelTeam: "mdm"}}}
	c := NewFakeClient(other)
	if _, err := Reconcile(ctx, c, riqXR()); err != nil {
		t.Fatal(err)
	}
	if _, ok := c.Get("team-mdm", KindInstance, "riq-scores-pg-old"); !ok {
		t.Fatalf("an XR with the same name in another namespace owns that resource; do not delete it")
	}
}

func TestHiddenClientErrorSurfaces(t *testing.T) {
	c := NewFakeClient()
	c.FailApply = errors.New("quota exceeded")
	out, err := Reconcile(context.Background(), c, riqXR())
	if err == nil {
		t.Fatalf("client errors must be returned so the controller requeues")
	}
	s := FindCondition(out.Conditions, "Synced")
	if s.Status != "False" || s.Reason != "ReconcileError" || !strings.Contains(s.Message, "quota exceeded") {
		t.Fatalf("Synced = %+v", s)
	}
}
