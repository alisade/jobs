package controller

import (
	"context"
	"testing"
	"time"

	. "github.com/onsi/gomega"
	"k8s.io/apimachinery/pkg/api/meta"

	agentsv1alpha1 "github.com/latticeai/agent-fleet-operator/api/v1alpha1"
)

// Visible reproduction of PLAT-PAGE-7731: one MCPServer that is Ready and unchanged
// should cost (almost) no reconciles. Production sees thousands per minute.
func TestReproSteadyStateReconcileRate(t *testing.T) {
	g := NewWithT(t)
	ns := newNamespace(t)
	g.Expect(k8sClient.Create(context.Background(), newMCPServer(ns, "github-tools"))).To(Succeed())
	g.Eventually(func(g Gomega) { setAvailable(g, ns, "github-tools", 2) }, timeout, interval).Should(Succeed())
	g.Eventually(func(g Gomega) {
		m := getMCP(g, ns, "github-tools")
		g.Expect(meta.IsStatusConditionTrue(m.Status.Conditions, agentsv1alpha1.ConditionReady)).To(BeTrue())
	}, timeout, interval).Should(Succeed())

	time.Sleep(500 * time.Millisecond) // let in-flight events drain
	start, rv0 := reconcileTotal(t), getMCP(g, ns, "github-tools").ResourceVersion
	time.Sleep(3 * time.Second) // measurement window, not synchronisation
	delta, rv1 := reconcileTotal(t)-start, getMCP(g, ns, "github-tools").ResourceVersion
	t.Logf("steady state over 3s: %.0f reconciles, resourceVersion %s -> %s", delta, rv0, rv1)
	if delta > 2 {
		t.Fatalf("hot loop: %.0f reconciles in 3s for one unchanged, Ready MCPServer (want <= 2)", delta)
	}
}
