package controller

import (
	"context"
	"testing"

	. "github.com/onsi/gomega"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/meta"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/utils/ptr"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"

	agentsv1alpha1 "github.com/latticeai/agent-fleet-operator/api/v1alpha1"
)

func getMCP(g Gomega, ns, name string) *agentsv1alpha1.MCPServer {
	var m agentsv1alpha1.MCPServer
	g.Expect(k8sClient.Get(context.Background(), client.ObjectKey{Namespace: ns, Name: name}, &m)).To(Succeed())
	return &m
}

func getService(g Gomega, ns, name string) *corev1.Service {
	var s corev1.Service
	g.Expect(k8sClient.Get(context.Background(), client.ObjectKey{Namespace: ns, Name: name}, &s)).To(Succeed())
	return &s
}

func catalog(g Gomega) map[string]string {
	var cm corev1.ConfigMap
	g.Expect(k8sClient.Get(context.Background(), client.ObjectKey{Namespace: catalogNamespace, Name: CatalogConfigMapName}, &cm)).To(Succeed())
	return cm.Data
}

func mcpContainer(g Gomega, d *appsv1.Deployment) corev1.Container {
	for _, c := range d.Spec.Template.Spec.Containers {
		if c.Name == ContainerName {
			return c
		}
	}
	g.Expect(d.Spec.Template.Spec.Containers).To(ContainElement(HaveField("Name", ContainerName)))
	return corev1.Container{}
}

func envValue(c corev1.Container, name string) string {
	for _, e := range c.Env {
		if e.Name == name {
			return e.Value
		}
	}
	return ""
}

// setAvailable simulates the Deployment controller, which envtest does not run.
func setAvailable(g Gomega, ns, name string, n int32) {
	d := getDeployment(g, ns, name)
	d.Status.Replicas = n
	d.Status.ReadyReplicas = n
	d.Status.AvailableReplicas = n
	d.Status.UpdatedReplicas = n
	d.Status.ObservedGeneration = d.Generation
	g.Expect(k8sClient.Status().Update(context.Background(), d)).To(Succeed())
}

func isOwnedBy(obj metav1.Object, owner *agentsv1alpha1.MCPServer) bool {
	ref := metav1.GetControllerOf(obj)
	return ref != nil && ref.UID == owner.UID && ref.Kind == "MCPServer" &&
		ref.APIVersion == agentsv1alpha1.GroupVersion.String() && ptr.Deref(ref.BlockOwnerDeletion, false)
}

func create(t *testing.T, mcp *agentsv1alpha1.MCPServer) {
	t.Helper()
	if err := k8sClient.Create(context.Background(), mcp); err != nil {
		t.Fatalf("create MCPServer: %v", err)
	}
}

func TestHiddenChildrenHaveControllerOwnerRefs(t *testing.T) {
	g := NewWithT(t)
	ns := newNamespace(t)
	mcp := newMCPServer(ns, "owned")
	create(t, mcp)
	g.Eventually(func(g Gomega) {
		m := getMCP(g, ns, "owned")
		g.Expect(isOwnedBy(getDeployment(g, ns, "owned"), m)).To(BeTrue(), "Deployment needs a controller owner ref to the MCPServer")
		g.Expect(isOwnedBy(getService(g, ns, "owned"), m)).To(BeTrue(), "Service needs a controller owner ref to the MCPServer")
	}, timeout, interval).Should(Succeed())
}

func TestHiddenDeploymentSpecFromMCPServer(t *testing.T) {
	g := NewWithT(t)
	ns := newNamespace(t)
	mcp := newMCPServer(ns, "spec")
	mcp.Spec.Port = 9090
	mcp.Spec.Replicas = ptr.To[int32](3)
	mcp.Spec.Transport = agentsv1alpha1.TransportSSE
	mcp.Spec.EnvFrom = []corev1.EnvFromSource{{SecretRef: &corev1.SecretEnvSource{
		LocalObjectReference: corev1.LocalObjectReference{Name: "github-token"}}}}
	create(t, mcp)
	g.Eventually(func(g Gomega) {
		d := getDeployment(g, ns, "spec")
		g.Expect(d.Spec.Replicas).To(HaveValue(Equal(int32(3))))
		g.Expect(d.Spec.Selector.MatchLabels).To(Equal(Labels(mcp)))
		g.Expect(d.Spec.Template.Labels).To(Equal(Labels(mcp)))
		c := mcpContainer(g, d)
		g.Expect(c.Image).To(Equal(mcp.Spec.Image))
		g.Expect(c.Ports).To(ContainElement(And(HaveField("Name", PortName), HaveField("ContainerPort", int32(9090)))))
		g.Expect(envValue(c, "MCP_TRANSPORT")).To(Equal("sse"))
		g.Expect(c.EnvFrom).To(HaveLen(1))
		g.Expect(c.EnvFrom[0].SecretRef).NotTo(BeNil())
		g.Expect(c.EnvFrom[0].SecretRef.Name).To(Equal("github-token"))
	}, timeout, interval).Should(Succeed())
}

func TestHiddenServiceTargetsNamedPort(t *testing.T) {
	g := NewWithT(t)
	ns := newNamespace(t)
	mcp := newMCPServer(ns, "svc")
	mcp.Spec.Port = 7000
	create(t, mcp)
	g.Eventually(func(g Gomega) {
		s := getService(g, ns, "svc")
		g.Expect(s.Spec.Selector).To(Equal(Labels(mcp)))
		g.Expect(s.Spec.Ports).To(HaveLen(1))
		g.Expect(s.Spec.Ports[0].Port).To(Equal(int32(7000)))
		g.Expect(s.Spec.Ports[0].Name).To(Equal(PortName))
		tp := s.Spec.Ports[0].TargetPort
		g.Expect(tp.StrVal == PortName || tp.IntVal == 7000).To(BeTrue(), "targetPort must reach the container port")
	}, timeout, interval).Should(Succeed())
}

func TestHiddenDeploymentDriftIsCorrected(t *testing.T) {
	g := NewWithT(t)
	ns := newNamespace(t)
	mcp := newMCPServer(ns, "drift")
	create(t, mcp)
	g.Eventually(func(g Gomega) { getDeployment(g, ns, "drift") }, timeout, interval).Should(Succeed())

	// Someone runs kubectl set image / scale on the child.
	g.Eventually(func(g Gomega) {
		d := getDeployment(g, ns, "drift")
		d.Spec.Template.Spec.Containers[0].Image = "attacker/mcp:latest"
		d.Spec.Replicas = ptr.To[int32](9)
		g.Expect(k8sClient.Update(context.Background(), d)).To(Succeed())
	}, timeout, interval).Should(Succeed())

	g.Eventually(func(g Gomega) {
		d := getDeployment(g, ns, "drift")
		g.Expect(mcpContainer(g, d).Image).To(Equal(mcp.Spec.Image), "drift on an owned Deployment must trigger a reconcile (Owns watch)")
		g.Expect(d.Spec.Replicas).To(HaveValue(Equal(int32(2))))
	}, timeout, interval).Should(Succeed())
}

func TestHiddenServiceDeletedIsRecreated(t *testing.T) {
	g := NewWithT(t)
	ns := newNamespace(t)
	create(t, newMCPServer(ns, "svc-gone"))
	var uid types.UID
	g.Eventually(func(g Gomega) { uid = getService(g, ns, "svc-gone").UID }, timeout, interval).Should(Succeed())
	g.Expect(k8sClient.Delete(context.Background(), &corev1.Service{ObjectMeta: metav1.ObjectMeta{Namespace: ns, Name: "svc-gone"}})).To(Succeed())
	g.Eventually(func(g Gomega) {
		g.Expect(getService(g, ns, "svc-gone").UID).NotTo(Equal(uid))
	}, timeout, interval).Should(Succeed())
}

func TestHiddenSpecChangeUpdatesChildren(t *testing.T) {
	g := NewWithT(t)
	ns := newNamespace(t)
	create(t, newMCPServer(ns, "upgrade"))
	g.Eventually(func(g Gomega) { getService(g, ns, "upgrade") }, timeout, interval).Should(Succeed())

	g.Eventually(func(g Gomega) {
		m := getMCP(g, ns, "upgrade")
		m.Spec.Image = "ghcr.io/latticeai/mcp-k8s-tools:1.5.0"
		m.Spec.Port = 8443
		g.Expect(k8sClient.Update(context.Background(), m)).To(Succeed())
	}, timeout, interval).Should(Succeed())

	g.Eventually(func(g Gomega) {
		g.Expect(mcpContainer(g, getDeployment(g, ns, "upgrade")).Image).To(Equal("ghcr.io/latticeai/mcp-k8s-tools:1.5.0"))
		g.Expect(getService(g, ns, "upgrade").Spec.Ports[0].Port).To(Equal(int32(8443)))
	}, timeout, interval).Should(Succeed())
}

func TestHiddenNotReadyUntilReplicasAvailable(t *testing.T) {
	g := NewWithT(t)
	ns := newNamespace(t)
	create(t, newMCPServer(ns, "rollout"))
	g.Eventually(func(g Gomega) {
		m := getMCP(g, ns, "rollout")
		ready := meta.FindStatusCondition(m.Status.Conditions, agentsv1alpha1.ConditionReady)
		g.Expect(ready).NotTo(BeNil(), "Ready condition missing")
		g.Expect(ready.Status).To(Equal(metav1.ConditionFalse))
		g.Expect(meta.IsStatusConditionTrue(m.Status.Conditions, agentsv1alpha1.ConditionProgressing)).To(BeTrue())
		g.Expect(meta.IsStatusConditionTrue(m.Status.Conditions, agentsv1alpha1.ConditionDegraded)).To(BeTrue(),
			"0 of 2 replicas available is Degraded")
	}, timeout, interval).Should(Succeed())

	// One of two up: still not Ready, still progressing, no longer degraded.
	g.Eventually(func(g Gomega) { setAvailable(g, ns, "rollout", 1) }, timeout, interval).Should(Succeed())
	g.Eventually(func(g Gomega) {
		m := getMCP(g, ns, "rollout")
		g.Expect(m.Status.AvailableReplicas).To(Equal(int32(1)))
		g.Expect(meta.IsStatusConditionFalse(m.Status.Conditions, agentsv1alpha1.ConditionReady)).To(BeTrue())
		g.Expect(meta.IsStatusConditionTrue(m.Status.Conditions, agentsv1alpha1.ConditionProgressing)).To(BeTrue())
		g.Expect(meta.IsStatusConditionFalse(m.Status.Conditions, agentsv1alpha1.ConditionDegraded)).To(BeTrue())
	}, timeout, interval).Should(Succeed())
}

func TestHiddenReadyWhenAvailableWithEndpoint(t *testing.T) {
	g := NewWithT(t)
	ns := newNamespace(t)
	mcp := newMCPServer(ns, "ready")
	create(t, mcp)
	g.Eventually(func(g Gomega) { setAvailable(g, ns, "ready", 2) }, timeout, interval).Should(Succeed())
	g.Eventually(func(g Gomega) {
		m := getMCP(g, ns, "ready")
		g.Expect(meta.IsStatusConditionTrue(m.Status.Conditions, agentsv1alpha1.ConditionReady)).To(BeTrue())
		g.Expect(meta.IsStatusConditionFalse(m.Status.Conditions, agentsv1alpha1.ConditionProgressing)).To(BeTrue())
		g.Expect(meta.IsStatusConditionFalse(m.Status.Conditions, agentsv1alpha1.ConditionDegraded)).To(BeTrue())
		g.Expect(m.Status.AvailableReplicas).To(Equal(int32(2)))
		g.Expect(m.Status.Endpoint).To(Equal("http://ready." + ns + ".svc.cluster.local:8080/mcp"))
		for _, c := range m.Status.Conditions {
			g.Expect(c.Reason).NotTo(BeEmpty())
		}
	}, timeout, interval).Should(Succeed())
}

func TestHiddenObservedGenerationTracksSpec(t *testing.T) {
	g := NewWithT(t)
	ns := newNamespace(t)
	create(t, newMCPServer(ns, "gen"))
	g.Eventually(func(g Gomega) {
		m := getMCP(g, ns, "gen")
		g.Expect(m.Status.ObservedGeneration).To(Equal(m.Generation))
	}, timeout, interval).Should(Succeed())

	g.Eventually(func(g Gomega) {
		m := getMCP(g, ns, "gen")
		m.Spec.Replicas = ptr.To[int32](4)
		g.Expect(k8sClient.Update(context.Background(), m)).To(Succeed())
	}, timeout, interval).Should(Succeed())

	g.Eventually(func(g Gomega) {
		m := getMCP(g, ns, "gen")
		g.Expect(m.Generation).To(BeNumerically(">=", 2))
		g.Expect(m.Status.ObservedGeneration).To(Equal(m.Generation))
		for _, c := range m.Status.Conditions {
			g.Expect(c.ObservedGeneration).To(Equal(m.Generation), "condition %s observedGeneration", c.Type)
		}
	}, timeout, interval).Should(Succeed())
}

func TestHiddenFinalizerAdded(t *testing.T) {
	g := NewWithT(t)
	ns := newNamespace(t)
	create(t, newMCPServer(ns, "fin"))
	g.Eventually(func(g Gomega) {
		g.Expect(getMCP(g, ns, "fin").Finalizers).To(ContainElement(FinalizerName))
	}, timeout, interval).Should(Succeed())
}

func TestHiddenCatalogRegistration(t *testing.T) {
	g := NewWithT(t)
	ns := newNamespace(t)
	create(t, newMCPServer(ns, "cat"))
	g.Eventually(func(g Gomega) {
		g.Expect(catalog(g)).To(HaveKeyWithValue(ns+".cat", "http://cat."+ns+".svc.cluster.local:8080/mcp"))
	}, timeout, interval).Should(Succeed())

	// Endpoint changes follow the spec.
	g.Eventually(func(g Gomega) {
		m := getMCP(g, ns, "cat")
		m.Spec.Path = "/v2/mcp"
		g.Expect(k8sClient.Update(context.Background(), m)).To(Succeed())
	}, timeout, interval).Should(Succeed())
	g.Eventually(func(g Gomega) {
		g.Expect(catalog(g)).To(HaveKeyWithValue(ns+".cat", "http://cat."+ns+".svc.cluster.local:8080/v2/mcp"))
	}, timeout, interval).Should(Succeed())
}

func TestHiddenDeleteDeregistersAndReleasesFinalizer(t *testing.T) {
	g := NewWithT(t)
	ns := newNamespace(t)
	create(t, newMCPServer(ns, "bye"))
	// Another server in the same catalog must survive.
	create(t, newMCPServer(ns, "stay"))
	g.Eventually(func(g Gomega) {
		g.Expect(catalog(g)).To(HaveKey(ns + ".bye"))
		g.Expect(catalog(g)).To(HaveKey(ns + ".stay"))
		g.Expect(getMCP(g, ns, "bye").Finalizers).To(ContainElement(FinalizerName))
	}, timeout, interval).Should(Succeed())

	g.Expect(k8sClient.Delete(context.Background(), &agentsv1alpha1.MCPServer{ObjectMeta: metav1.ObjectMeta{Namespace: ns, Name: "bye"}})).To(Succeed())
	g.Eventually(func(g Gomega) {
		err := k8sClient.Get(context.Background(), client.ObjectKey{Namespace: ns, Name: "bye"}, &agentsv1alpha1.MCPServer{})
		g.Expect(apierrors.IsNotFound(err)).To(BeTrue(), "MCPServer should be gone once the finalizer is released, got %v", err)
	}, timeout, interval).Should(Succeed())
	g.Expect(catalog(g)).NotTo(HaveKey(ns + ".bye"))
	g.Expect(catalog(g)).To(HaveKey(ns + ".stay"))
}

func TestHiddenDeleteDoesNotHangWhenCatalogEntryMissing(t *testing.T) {
	g := NewWithT(t)
	ns := newNamespace(t)
	create(t, newMCPServer(ns, "orphan"))
	g.Eventually(func(g Gomega) {
		g.Expect(catalog(g)).To(HaveKey(ns + ".orphan"))
	}, timeout, interval).Should(Succeed())

	// A human removed the entry by hand; deletion must still complete.
	g.Eventually(func(g Gomega) {
		var cm corev1.ConfigMap
		g.Expect(k8sClient.Get(context.Background(), client.ObjectKey{Namespace: catalogNamespace, Name: CatalogConfigMapName}, &cm)).To(Succeed())
		delete(cm.Data, ns+".orphan")
		g.Expect(k8sClient.Update(context.Background(), &cm)).To(Succeed())
	}, timeout, interval).Should(Succeed())
	g.Expect(k8sClient.Delete(context.Background(), &agentsv1alpha1.MCPServer{ObjectMeta: metav1.ObjectMeta{Namespace: ns, Name: "orphan"}})).To(Succeed())
	g.Eventually(func(g Gomega) {
		err := k8sClient.Get(context.Background(), client.ObjectKey{Namespace: ns, Name: "orphan"}, &agentsv1alpha1.MCPServer{})
		g.Expect(apierrors.IsNotFound(err)).To(BeTrue())
	}, timeout, interval).Should(Succeed())
}

func TestHiddenReconcileNotFoundIsNoError(t *testing.T) {
	res, err := reconciler.Reconcile(context.Background(), ctrl.Request{NamespacedName: types.NamespacedName{Namespace: "nowhere", Name: "ghost"}})
	if err != nil {
		t.Fatalf("Reconcile of a deleted object must return nil error, got %v", err)
	}
	if res.RequeueAfter != 0 {
		t.Fatalf("Reconcile of a deleted object must not requeue, got %+v", res)
	}
}

func TestHiddenSteadyStateDoesNotRewriteStatus(t *testing.T) {
	g := NewWithT(t)
	ns := newNamespace(t)
	create(t, newMCPServer(ns, "steady"))
	g.Eventually(func(g Gomega) { setAvailable(g, ns, "steady", 2) }, timeout, interval).Should(Succeed())
	var rv string
	g.Eventually(func(g Gomega) {
		m := getMCP(g, ns, "steady")
		g.Expect(meta.IsStatusConditionTrue(m.Status.Conditions, agentsv1alpha1.ConditionReady)).To(BeTrue())
		rv = m.ResourceVersion
	}, timeout, interval).Should(Succeed())
	// Re-running reconcile with nothing changed must be a no-op on the API server.
	for range 3 {
		_, err := reconciler.Reconcile(context.Background(), ctrl.Request{NamespacedName: types.NamespacedName{Namespace: ns, Name: "steady"}})
		g.Expect(err).NotTo(HaveOccurred())
	}
	g.Consistently(func(g Gomega) {
		g.Expect(getMCP(g, ns, "steady").ResourceVersion).To(Equal(rv), "steady-state reconcile wrote to the MCPServer")
	}, "1s", interval).Should(Succeed())
}
