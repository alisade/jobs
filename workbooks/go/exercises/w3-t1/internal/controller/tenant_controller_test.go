package controller

import (
	"context"
	"testing"
	"time"

	corev1 "k8s.io/api/core/v1"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

func TestDesiredQuota(t *testing.T) {
	tn := newTenant("team-a", "ml")
	q, err := DesiredQuota(tn)
	if err != nil {
		t.Fatal(err)
	}
	if got := q.Spec.Hard[corev1.ResourceRequestsCPU]; got.String() != "8" {
		t.Fatalf("cpu = %s", got.String())
	}
	tn.Spec.Memory = "lots"
	if _, err := DesiredQuota(tn); err == nil {
		t.Fatal("expected an error for an invalid quantity")
	}
}

// TestReconcileEndToEnd runs the controller against a real kube-apiserver (envtest)
// and checks the Tenant's children and Ready condition.
func TestReconcileEndToEnd(t *testing.T) {
	startManager(t, adminCfg)
	ns := newNamespace(t, "analytics")
	tn := newTenant(ns, "forecasting")
	if err := adminClient.Create(context.Background(), tn); err != nil {
		t.Fatal(err)
	}
	key := client.ObjectKeyFromObject(tn)
	waitFor(t, 30*time.Second, "Tenant Ready=True", func() bool { return tenantReady(t, adminClient, key) })

	var s corev1.Secret
	if err := adminClient.Get(context.Background(), client.ObjectKey{Namespace: ns, Name: SecretName(tn)}, &s); err != nil {
		t.Fatalf("storage secret: %v", err)
	}
	if string(s.Data["prefix"]) != "forecasting/" {
		t.Fatalf("prefix = %q", s.Data["prefix"])
	}
}
