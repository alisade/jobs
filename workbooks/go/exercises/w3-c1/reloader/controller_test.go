package reloader

import (
	"context"
	"testing"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// Visible test: the happy path. Run with `make test`.
func TestConfigMapChangeRollsReferencingDeployment(t *testing.T) {
	cm := configMap("payments", "ledger-config", true, map[string]string{"LOG_LEVEL": "info"})
	h := newHarness(t, fastOpts(), nil, cm, deployment("payments", "ledger-api", "ledger-config", nil))
	h.start()

	key := HashAnnotationPrefix + "ledger-config"
	first := ""
	eventually(t, "ledger-api gets the initial hash annotation", func() bool {
		first = h.deployment("payments", "ledger-api").Spec.Template.Annotations[key]
		return first != ""
	})
	if first != HashConfigMap(cm) {
		t.Fatalf("annotation = %q, want HashConfigMap(cm) = %q", first, HashConfigMap(cm))
	}

	cm.Data["LOG_LEVEL"] = "debug"
	cm.ResourceVersion = "2"
	if _, err := h.client.CoreV1().ConfigMaps("payments").Update(context.Background(), cm, metav1.UpdateOptions{}); err != nil {
		t.Fatal(err)
	}
	eventually(t, "annotation changes after the ConfigMap changes", func() bool {
		got := h.deployment("payments", "ledger-api").Spec.Template.Annotations[key]
		return got != "" && got != first
	})
}

func TestHashConfigMapIsStableAndContentSensitive(t *testing.T) {
	a := configMap("ns", "a", true, map[string]string{"x": "1", "y": "2", "z": "3"})
	b := configMap("ns", "b", false, map[string]string{"z": "3", "y": "2", "x": "1"})
	if HashConfigMap(a) == "" || HashConfigMap(a) != HashConfigMap(b) {
		t.Fatalf("same data must hash the same regardless of name/labels/order: %q vs %q", HashConfigMap(a), HashConfigMap(b))
	}
	b.Data["x"] = "changed"
	if HashConfigMap(a) == HashConfigMap(b) {
		t.Fatal("different data must hash differently")
	}
}
