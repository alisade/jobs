package controller

import (
	"context"
	"testing"
	"time"

	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/meta"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/rest"
	"k8s.io/utils/ptr"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/config"
	metricsserver "sigs.k8s.io/controller-runtime/pkg/metrics/server"

	platformv1alpha1 "github.com/harbor-analytics/tenant-operator/api/v1alpha1"
)

// startManager runs the Tenant controller with the given identity until the test ends.
func startManager(t *testing.T, cfg *rest.Config) {
	t.Helper()
	mgr, err := ctrl.NewManager(cfg, ctrl.Options{
		Scheme:         testScheme,
		Metrics:        metricsserver.Options{BindAddress: "0"},
		LeaderElection: false,
		Controller: config.Controller{
			SkipNameValidation: ptr.To(true),
			CacheSyncTimeout:   15 * time.Second,
		},
	})
	if err != nil {
		t.Fatalf("new manager: %v", err)
	}
	r := &TenantReconciler{Client: mgr.GetClient(), Scheme: mgr.GetScheme(), Recorder: mgr.GetEventRecorder("tenant-operator")}
	if err := r.SetupWithManager(mgr); err != nil {
		t.Fatalf("setup: %v", err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan error, 1)
	go func() { done <- mgr.Start(ctx) }()
	t.Cleanup(func() {
		cancel()
		select {
		case err := <-done:
			if err != nil {
				t.Logf("manager exited with: %v", err)
			}
		case <-time.After(10 * time.Second):
		}
	})
}

func newNamespace(t *testing.T, prefix string) string {
	t.Helper()
	ns := &corev1.Namespace{ObjectMeta: metav1.ObjectMeta{GenerateName: prefix + "-"}}
	if err := adminClient.Create(context.Background(), ns); err != nil {
		t.Fatalf("create namespace: %v", err)
	}
	return ns.Name
}

func newTenant(ns, name string) *platformv1alpha1.Tenant {
	return &platformv1alpha1.Tenant{
		ObjectMeta: metav1.ObjectMeta{Namespace: ns, Name: name},
		Spec:       platformv1alpha1.TenantSpec{CPU: "8", Memory: "32Gi", BucketPrefix: name + "/"},
	}
}

// waitFor polls cond every 250ms until it returns true or timeout passes.
func waitFor(t *testing.T, timeout time.Duration, what string, cond func() bool) {
	t.Helper()
	deadline := time.Now().Add(timeout)
	for time.Now().Before(deadline) {
		if cond() {
			return
		}
		time.Sleep(250 * time.Millisecond)
	}
	t.Fatalf("timed out after %s waiting for: %s", timeout, what)
}

func tenantReady(t *testing.T, c client.Client, key client.ObjectKey) bool {
	var got platformv1alpha1.Tenant
	if err := c.Get(context.Background(), key, &got); err != nil {
		return false
	}
	return meta.IsStatusConditionTrue(got.Status.Conditions, ConditionReady)
}
