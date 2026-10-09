package meshsim

import "testing"

// Visible checks. They load manifests/ plus the installed injector webhook from
// artifacts/istio/ and replay the call that is failing in production.

func load(t *testing.T) *Cluster {
	t.Helper()
	c, err := Load("..")
	if err != nil {
		t.Fatalf("manifests do not parse: %v", err)
	}
	return c
}

func TestManifestsParse(t *testing.T) {
	c := load(t)
	for _, ns := range []string{"agents", "mcp-tools"} {
		if _, ok := c.Namespaces[ns]; !ok {
			t.Fatalf("namespace %s missing", ns)
		}
	}
	if len(c.Webhooks) == 0 {
		t.Fatal("injector webhook artifact missing")
	}
}

func TestAgentRuntimeCanCallMCP(t *testing.T) {
	c := load(t)
	src, err := c.FromDeployment("agents", "agent-runtime")
	if err != nil {
		t.Fatal(err)
	}
	dst, err := c.ServiceWorkload("mcp-tools", "k8s-tools")
	if err != nil {
		t.Fatal(err)
	}
	for _, m := range []string{"POST", "GET", "DELETE"} {
		res := c.Call(src, dst, m, "/mcp")
		t.Logf("agent-runtime -> k8s-tools %s /mcp: %s", m, res)
		if res.Status != 200 {
			t.Errorf("%s /mcp: got %s, want 200", m, res)
		}
	}
}
