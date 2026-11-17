package controller

import (
	"context"
	"testing"

	. "github.com/onsi/gomega"
)

// Visible test: creating an MCPServer produces a Deployment running its image.
func TestCreatesDeployment(t *testing.T) {
	g := NewWithT(t)
	ns := newNamespace(t)
	mcp := newMCPServer(ns, "k8s-tools")
	g.Expect(k8sClient.Create(context.Background(), mcp)).To(Succeed())

	g.Eventually(func(g Gomega) {
		d := getDeployment(g, ns, "k8s-tools")
		g.Expect(d.Spec.Template.Spec.Containers).NotTo(BeEmpty())
		g.Expect(d.Spec.Template.Spec.Containers[0].Image).To(Equal(mcp.Spec.Image))
	}, timeout, interval).Should(Succeed())
}
