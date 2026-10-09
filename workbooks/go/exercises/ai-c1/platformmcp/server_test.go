package platformmcp

import (
	"strings"
	"testing"
)

// Visible test: a read-only token can list deployments over streamable HTTP.
func TestReadTokenListsDeployments(t *testing.T) {
	base, _ := startServer(t)
	cs := mustConnect(t, base, "read-token")
	res, err := call(t, cs, "list_deployments", map[string]any{"namespace": "shop"})
	if err != nil {
		t.Fatalf("CallTool: %v", err)
	}
	if res.IsError {
		t.Fatalf("tool error: %s", resultText(res))
	}
	if txt := resultText(res); !strings.Contains(txt, "checkout") || !strings.Contains(txt, "cart") {
		t.Fatalf("result = %s, want checkout and cart", txt)
	}
}
