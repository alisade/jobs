package controller

import (
	"context"
	"fmt"
	"testing"
	"time"

	. "github.com/onsi/gomega"
	"k8s.io/apimachinery/pkg/api/meta"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/utils/ptr"
	ctrl "sigs.k8s.io/controller-runtime"

	agentsv1alpha1 "github.com/latticeai/agent-fleet-operator/api/v1alpha1"
)

func readyServers(t *testing.T, g *WithT, ns string, names ...string) {
	t.Helper()
	for _, n := range names {
		g.Expect(k8sClient.Create(context.Background(), newMCPServer(ns, n))).To(Succeed())
	}
	for _, n := range names {
		g.Eventually(func(g Gomega) { setAvailable(g, ns, n, 2) }, timeout, interval).Should(Succeed())
	}
	for _, n := range names {
		g.Eventually(func(g Gomega) {
			m := getMCP(g, ns, n)
			g.Expect(meta.IsStatusConditionTrue(m.Status.Conditions, agentsv1alpha1.ConditionReady)).To(BeTrue())
			g.Expect(m.Status.ObservedGeneration).To(Equal(m.Generation))
		}, timeout, interval).Should(Succeed())
	}
	time.Sleep(500 * time.Millisecond) // drain in-flight events before measuring
}

func TestHiddenNoHotLoopAcrossManyServers(t *testing.T) {
	g := NewWithT(t)
	ns := newNamespace(t)
	names := []string{"a", "b", "c", "d", "e"}
	readyServers(t, g, ns, names...)
	start := reconcileTotal(t)
	time.Sleep(3 * time.Second) // measurement window
	delta := reconcileTotal(t) - start
	if delta > 3 {
		t.Fatalf("%.0f reconciles in 3s for 5 unchanged Ready servers (want <= 3)", delta)
	}
}

func TestHiddenSteadyStateNoStatusWrites(t *testing.T) {
	g := NewWithT(t)
	ns := newNamespace(t)
	readyServers(t, g, ns, "quiet")
	rv := getMCP(g, ns, "quiet").ResourceVersion
	g.Consistently(func(g Gomega) {
		g.Expect(getMCP(g, ns, "quiet").ResourceVersion).To(Equal(rv), "MCPServer is being written at steady state")
	}, "2s", "200ms").Should(Succeed())
}

// A predicate alone hides the loop but every legitimate reconcile (resync, child event,
// operator restart) still writes status. The reconcile itself must be a no-op.
func TestHiddenDirectReconcileIsNoOp(t *testing.T) {
	g := NewWithT(t)
	ns := newNamespace(t)
	readyServers(t, g, ns, "noop")
	rv := getMCP(g, ns, "noop").ResourceVersion
	for i := range 5 {
		_, err := reconciler.Reconcile(context.Background(), ctrl.Request{NamespacedName: types.NamespacedName{Namespace: ns, Name: "noop"}})
		g.Expect(err).NotTo(HaveOccurred(), fmt.Sprintf("reconcile %d", i))
	}
	g.Consistently(func(g Gomega) {
		g.Expect(getMCP(g, ns, "noop").ResourceVersion).To(Equal(rv), "steady-state Reconcile wrote to the MCPServer")
	}, "1s", "200ms").Should(Succeed())
}

func TestHiddenSpecChangeStillReconciles(t *testing.T) {
	g := NewWithT(t)
	ns := newNamespace(t)
	readyServers(t, g, ns, "upgrade")
	g.Eventually(func(g Gomega) {
		m := getMCP(g, ns, "upgrade")
		m.Spec.Image = "ghcr.io/latticeai/mcp-k8s-tools:1.5.0"
		g.Expect(k8sClient.Update(context.Background(), m)).To(Succeed())
	}, timeout, interval).Should(Succeed())
	g.Eventually(func(g Gomega) {
		d := getDeployment(g, ns, "upgrade")
		g.Expect(d.Spec.Template.Spec.Containers[0].Image).To(Equal("ghcr.io/latticeai/mcp-k8s-tools:1.5.0"))
		m := getMCP(g, ns, "upgrade")
		g.Expect(m.Status.ObservedGeneration).To(Equal(m.Generation))
	}, timeout, interval).Should(Succeed())
}

func TestHiddenChildDriftStillCorrected(t *testing.T) {
	g := NewWithT(t)
	ns := newNamespace(t)
	readyServers(t, g, ns, "drift")
	g.Eventually(func(g Gomega) {
		d := getDeployment(g, ns, "drift")
		d.Spec.Replicas = ptr.To[int32](7)
		g.Expect(k8sClient.Update(context.Background(), d)).To(Succeed())
	}, timeout, interval).Should(Succeed())
	g.Eventually(func(g Gomega) {
		g.Expect(getDeployment(g, ns, "drift").Spec.Replicas).To(HaveValue(Equal(int32(2))))
	}, timeout, interval).Should(Succeed())
}

// A global WithEventFilter(GenerationChangedPredicate{}) also filters Deployment status
// events, so Ready never follows availability. This must keep working.
func TestHiddenDeploymentStatusStillDrivesReady(t *testing.T) {
	g := NewWithT(t)
	ns := newNamespace(t)
	readyServers(t, g, ns, "avail")
	g.Eventually(func(g Gomega) { setAvailable(g, ns, "avail", 0) }, timeout, interval).Should(Succeed())
	g.Eventually(func(g Gomega) {
		m := getMCP(g, ns, "avail")
		g.Expect(meta.IsStatusConditionFalse(m.Status.Conditions, agentsv1alpha1.ConditionReady)).To(BeTrue(),
			"Ready must go False when the Deployment loses its replicas")
		g.Expect(meta.IsStatusConditionTrue(m.Status.Conditions, agentsv1alpha1.ConditionDegraded)).To(BeTrue())
	}, timeout, interval).Should(Succeed())
	g.Eventually(func(g Gomega) { setAvailable(g, ns, "avail", 2) }, timeout, interval).Should(Succeed())
	g.Eventually(func(g Gomega) {
		m := getMCP(g, ns, "avail")
		g.Expect(meta.IsStatusConditionTrue(m.Status.Conditions, agentsv1alpha1.ConditionReady)).To(BeTrue())
		g.Expect(m.Status.AvailableReplicas).To(Equal(int32(2)))
	}, timeout, interval).Should(Succeed())
}

func TestHiddenStatusStillComplete(t *testing.T) {
	g := NewWithT(t)
	ns := newNamespace(t)
	readyServers(t, g, ns, "status")
	m := getMCP(g, ns, "status")
	g.Expect(m.Status.Endpoint).To(Equal("http://status." + ns + ".svc.cluster.local:8080/mcp"))
	for _, typ := range []string{agentsv1alpha1.ConditionReady, agentsv1alpha1.ConditionProgressing, agentsv1alpha1.ConditionDegraded} {
		c := meta.FindStatusCondition(m.Status.Conditions, typ)
		g.Expect(c).NotTo(BeNil(), typ)
		g.Expect(c.ObservedGeneration).To(Equal(m.Generation), typ)
	}
}
