package meshsim

import (
	"crypto/sha256"
	"encoding/hex"
	"os"
	"path/filepath"
	"slices"
	"strings"
	"testing"
)

const hiddenRevision = "1-27-1"

func hiddenLoad(t *testing.T) *Cluster {
	t.Helper()
	c, err := Load("..")
	if err != nil {
		t.Fatalf("manifests do not parse: %v", err)
	}
	return c
}

func hiddenPair(t *testing.T, c *Cluster) (Workload, Workload) {
	t.Helper()
	src, err := c.FromDeployment("agents", "agent-runtime")
	if err != nil {
		t.Fatal(err)
	}
	dst, err := c.ServiceWorkload("mcp-tools", "k8s-tools")
	if err != nil {
		t.Fatal(err)
	}
	return src, dst
}

func TestHiddenAgentsNamespaceUsesRevisionLabel(t *testing.T) {
	c := hiddenLoad(t)
	ns := c.Namespaces["agents"]
	if ns == nil {
		t.Fatal("agents namespace missing")
	}
	if got := ns.Labels["istio.io/rev"]; got != hiddenRevision {
		t.Fatalf("agents istio.io/rev = %q, want %q (the installed revision)", got, hiddenRevision)
	}
	if _, ok := ns.Labels["istio-injection"]; ok {
		t.Fatal("agents still has istio-injection; it takes precedence and disables revision injection")
	}
	if ns.Labels["team"] != "agent-platform" || ns.Labels["pod-security.kubernetes.io/enforce"] != "restricted" {
		t.Fatal("other namespace labels must be preserved")
	}
}

func TestHiddenNoLegacyInjectionLabels(t *testing.T) {
	c := hiddenLoad(t)
	for name, ns := range c.Namespaces {
		if v, ok := ns.Labels["istio-injection"]; ok && v != "disabled" {
			t.Fatalf("namespace %s uses istio-injection=%s; the mesh has no default revision tag (ADR-017)", name, v)
		}
	}
	if _, ok := c.Namespaces["batch"].Labels["istio.io/rev"]; ok {
		t.Fatal("batch is out of the mesh by design; do not enrol it")
	}
}

func TestHiddenAllowPolicyNotWeakened(t *testing.T) {
	c := hiddenLoad(t)
	var allow []*AuthorizationPolicy
	for _, p := range c.AuthorizationPolicies {
		if p.Metadata.Namespace == "mcp-tools" && (p.Spec.Action == "" || strings.EqualFold(p.Spec.Action, "ALLOW")) {
			allow = append(allow, p)
		}
		if p.Metadata.Namespace == RootNamespace {
			t.Fatalf("mesh-wide AuthorizationPolicy %s added; fix the root cause instead", p.Metadata.Name)
		}
	}
	if len(allow) != 1 || allow[0].Metadata.Name != "k8s-tools-allow-agents" {
		t.Fatalf("want exactly the k8s-tools-allow-agents ALLOW policy in mcp-tools, got %d", len(allow))
	}
	p := allow[0]
	if p.Spec.Selector == nil || p.Spec.Selector.MatchLabels["app"] != "k8s-tools" {
		t.Fatal("ALLOW policy selector changed")
	}
	if len(p.Spec.Rules) != 1 || len(p.Spec.Rules[0].From) != 1 || len(p.Spec.Rules[0].To) != 1 {
		t.Fatal("ALLOW policy rules restructured")
	}
	s := p.Spec.Rules[0].From[0].Source
	if !slices.Equal(s.Principals, []string{"cluster.local/ns/agents/sa/agent-runtime"}) {
		t.Fatalf("principals = %v; must stay exactly the agent-runtime identity", s.Principals)
	}
	if len(s.Namespaces)+len(s.NotPrincipals)+len(s.NotNamespaces)+len(s.RequestPrincipals) != 0 {
		t.Fatal("extra source fields added to the ALLOW rule")
	}
	op := p.Spec.Rules[0].To[0].Operation
	if !slices.Equal(op.Methods, []string{"POST", "GET", "DELETE"}) || !slices.Equal(op.Paths, []string{"/mcp", "/mcp/*"}) {
		t.Fatalf("operation changed: methods=%v paths=%v", op.Methods, op.Paths)
	}
}

func TestHiddenDenyAdminPolicyKept(t *testing.T) {
	c := hiddenLoad(t)
	src, dst := hiddenPair(t, c)
	res := c.Call(src, dst, "POST", "/admin/reload")
	if res.Status != 403 || !strings.Contains(res.Details, "k8s-tools-deny-admin") {
		t.Fatalf("admin path must still be denied by k8s-tools-deny-admin, got %s", res)
	}
}

func TestHiddenPeerAuthenticationStrict(t *testing.T) {
	c := hiddenLoad(t)
	_, dst := hiddenPair(t, c)
	if m := c.peerAuthMode(dst); m != "STRICT" {
		t.Fatalf("effective mTLS mode for k8s-tools = %s, want STRICT", m)
	}
	for _, p := range c.PeerAuthentications {
		if p.Metadata.Namespace == RootNamespace && p.Spec.Mtls != nil && strings.ToUpper(p.Spec.Mtls.Mode) != "PERMISSIVE" {
			t.Fatal("do not flip the mesh-wide default; batch and other unmeshed namespaces depend on it")
		}
	}
}

func TestHiddenRequestAuthenticationUnchanged(t *testing.T) {
	c := hiddenLoad(t)
	if len(c.RequestAuthentications) != 1 {
		t.Fatalf("want the k8s-tools-jwt RequestAuthentication kept, found %d", len(c.RequestAuthentications))
	}
	ra := c.RequestAuthentications[0]
	if ra.Metadata.Name != "k8s-tools-jwt" || len(ra.Spec.JWTRules) != 1 {
		t.Fatal("RequestAuthentication changed")
	}
	r := ra.Spec.JWTRules[0]
	if r.Issuer != "https://oidc.eks.us-east-1.amazonaws.com/id/7F3C1A0B9D2E4F6A8B0C1D2E3F4A5B6C" ||
		!slices.Equal(r.Audiences, []string{"k8s-tools.mcp.kestrel.internal"}) ||
		!strings.HasSuffix(r.JwksURI, "/keys") {
		t.Fatalf("JWT rule changed: %+v (it was not the problem)", r)
	}
}

func TestHiddenAgentRuntimeAllowedAllMethods(t *testing.T) {
	c := hiddenLoad(t)
	src, dst := hiddenPair(t, c)
	if !src.Sidecar {
		t.Fatal("new agent-runtime pods would still start without a sidecar")
	}
	for _, m := range []string{"POST", "GET", "DELETE"} {
		for _, p := range []string{"/mcp", "/mcp/messages"} {
			if res := c.Call(src, dst, m, p); res.Status != 200 || !res.MTLS {
				t.Fatalf("%s %s: %s", m, p, res)
			}
		}
	}
}

func TestHiddenOtherServiceAccountDenied(t *testing.T) {
	c := hiddenLoad(t)
	_, dst := hiddenPair(t, c)
	src, err := c.FromDeployment("agents", "eval-runner")
	if err != nil {
		t.Fatal(err)
	}
	if !src.Sidecar {
		t.Fatal("eval-runner should be meshed too once the namespace is fixed")
	}
	if res := c.Call(src, dst, "POST", "/mcp"); res.Status != 403 {
		t.Fatalf("eval-runner (sa default) must be denied, got %s", res)
	}
}

func TestHiddenUnmeshedCallerRejected(t *testing.T) {
	c := hiddenLoad(t)
	_, dst := hiddenPair(t, c)
	src := c.Pod("batch", "spark", map[string]string{"app": "spark-driver"})
	if src.Sidecar {
		t.Fatal("batch must stay out of the mesh")
	}
	if res := c.Call(src, dst, "POST", "/mcp"); res.Status != 0 {
		t.Fatalf("plaintext caller should be rejected at the transport layer (STRICT), got %s", res)
	}
}

func TestHiddenDeploymentNotOptedOut(t *testing.T) {
	c := hiddenLoad(t)
	d := c.Deployments["agents/agent-runtime"]
	if d == nil {
		t.Fatal("agent-runtime deployment missing")
	}
	if d.Spec.Template.Labels["sidecar.istio.io/inject"] == "false" || d.Spec.Template.Annotations["sidecar.istio.io/inject"] == "false" {
		t.Fatal("agent-runtime opted out of injection")
	}
	if d.Spec.Template.Spec.ServiceAccountName != "agent-runtime" {
		t.Fatal("service account changed; the identity in the policy is the contract")
	}
}

func TestHiddenEvidenceAndModelUntouched(t *testing.T) {
	for path, want := range hiddenSums {
		b, err := os.ReadFile(filepath.Join("..", path))
		if err != nil {
			t.Fatalf("%s: %v", path, err)
		}
		sum := sha256.Sum256(b)
		if hex.EncodeToString(sum[:]) != want {
			t.Fatalf("%s was edited; fix the manifests, not the installed webhook or the model", path)
		}
	}
}
