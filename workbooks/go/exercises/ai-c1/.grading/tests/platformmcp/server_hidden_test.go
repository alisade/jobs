package platformmcp

import (
	"encoding/json"
	"io"
	"net/http"
	"slices"
	"strings"
	"testing"
)

const initBody = `{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"curl","version":"1"}}}`

func rawPost(t *testing.T, url, authz, session, body string) *http.Response {
	t.Helper()
	req, err := http.NewRequest(http.MethodPost, url, strings.NewReader(body))
	if err != nil {
		t.Fatal(err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json, text/event-stream")
	if authz != "" {
		req.Header.Set("Authorization", authz)
	}
	if session != "" {
		req.Header.Set("Mcp-Session-Id", session)
		req.Header.Set("Mcp-Protocol-Version", "2025-06-18")
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { resp.Body.Close() })
	return resp
}

func wantChallenge(t *testing.T, resp *http.Response, code int) {
	t.Helper()
	if resp.StatusCode != code {
		b, _ := io.ReadAll(resp.Body)
		t.Fatalf("status = %d (%s), want %d", resp.StatusCode, strings.TrimSpace(string(b)), code)
	}
	h := resp.Header.Get("WWW-Authenticate")
	if !strings.HasPrefix(h, "Bearer") || !strings.Contains(h, `resource_metadata="`+testMetadataURL+`"`) {
		t.Fatalf("WWW-Authenticate = %q, want Bearer with resource_metadata=%q (MCP authorization spec, RFC 9728)", h, testMetadataURL)
	}
}

func TestHiddenMetadataEndpointIsPublicRFC9728(t *testing.T) {
	base, _ := startServer(t)
	resp, err := http.Get(base + MetadataPath)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		t.Fatalf("metadata status = %d, want 200 without a token", resp.StatusCode)
	}
	var m struct {
		Resource             string   `json:"resource"`
		AuthorizationServers []string `json:"authorization_servers"`
		ScopesSupported      []string `json:"scopes_supported"`
		BearerMethods        []string `json:"bearer_methods_supported"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&m); err != nil {
		t.Fatalf("metadata is not JSON: %v", err)
	}
	if m.Resource != testResource || !slices.Contains(m.AuthorizationServers, "https://idp.kestrel.dev") {
		t.Fatalf("metadata = %+v", m)
	}
	if !slices.Contains(m.ScopesSupported, ScopeRead) || !slices.Contains(m.ScopesSupported, ScopeWrite) {
		t.Fatalf("scopes_supported = %v", m.ScopesSupported)
	}
	if !slices.Equal(m.BearerMethods, []string{"header"}) {
		t.Fatalf("bearer_methods_supported = %v, want [header]", m.BearerMethods)
	}
}

func TestHiddenNoTokenIs401WithResourceMetadata(t *testing.T) {
	base, _ := startServer(t)
	wantChallenge(t, rawPost(t, base+"/mcp", "", "", initBody), 401)
	wantChallenge(t, rawPost(t, base+"/mcp", "Basic YWxpY2U6cHc=", "", initBody), 401)
	// Tokens in the query string must never be accepted (MCP spec).
	wantChallenge(t, rawPost(t, base+"/mcp?access_token=read-token", "", "", initBody), 401)
	if _, err := connect(t, base, ""); err == nil {
		t.Fatal("client connected without a token")
	}
}

func TestHiddenInvalidAndExpiredTokensAre401(t *testing.T) {
	base, _ := startServer(t)
	for _, tok := range []string{"forged-token", "expired"} {
		wantChallenge(t, rawPost(t, base+"/mcp", "Bearer "+tok, "", initBody), 401)
	}
}

func TestHiddenWrongAudienceRejected(t *testing.T) {
	// A token minted for Grafana must not work here even with every scope:
	// no token passthrough / confused deputy.
	base, _ := startServer(t)
	wantChallenge(t, rawPost(t, base+"/mcp", "Bearer other-aud", "", initBody), 401)
	if _, err := connect(t, base, "other-aud"); err == nil {
		t.Fatal("token for another audience was accepted")
	}
}

func TestHiddenNoPlatformScopeIs403(t *testing.T) {
	base, _ := startServer(t)
	resp := rawPost(t, base+"/mcp", "Bearer no-scope", "", initBody)
	wantChallenge(t, resp, 403)
	if h := resp.Header.Get("WWW-Authenticate"); !strings.Contains(h, ScopeRead) {
		t.Fatalf("403 challenge should name the missing scope: %q", h)
	}
}

func TestHiddenVerifierOutageIsNot401(t *testing.T) {
	// 401 tells clients to throw the token away and re-run OAuth. When the
	// JWKS endpoint is down, that is the wrong signal: return 5xx.
	base, _ := startServer(t)
	resp := rawPost(t, base+"/mcp", "Bearer jwks-down", "", initBody)
	if resp.StatusCode < 500 {
		t.Fatalf("status = %d, want 5xx when the verifier cannot decide", resp.StatusCode)
	}
}

func TestHiddenWriteImpliesReadAndToolsListed(t *testing.T) {
	base, _ := startServer(t)
	cs := mustConnect(t, base, "write-token")
	res, err := call(t, cs, "get_rollout_status", map[string]any{"namespace": "shop", "name": "checkout"})
	if err != nil || res.IsError {
		t.Fatalf("write token should be able to read: err=%v res=%v", err, res)
	}
	if !strings.Contains(resultText(res), "CrashLoopBackOff") {
		t.Fatalf("rollout status text = %s", resultText(res))
	}

	ro := mustConnect(t, base, "read-token")
	lt, err := ro.ListTools(t.Context(), nil)
	if err != nil {
		t.Fatal(err)
	}
	var names []string
	for _, tl := range lt.Tools {
		names = append(names, tl.Name)
		if tl.Description == "" {
			t.Errorf("tool %s has no description", tl.Name)
		}
	}
	slices.Sort(names)
	if !slices.Equal(names, []string{"get_rollout_status", "list_deployments", "restart_deployment"}) {
		t.Fatalf("tools/list = %v, want all three tools (authorization is enforced at call time)", names)
	}
}

func TestHiddenReadOnlyTokenCannotRestart(t *testing.T) {
	base, p := startServer(t)
	cs := mustConnect(t, base, "read-token")
	res, err := call(t, cs, "restart_deployment", map[string]any{
		"namespace": "shop", "name": "checkout",
		"reason": "pods crash looping after 2.14.1, restart to pick up fixed config",
	})
	if err != nil {
		t.Fatalf("authorization failure should be a tool error the model can explain, not a protocol error: %v", err)
	}
	if !res.IsError || !strings.Contains(resultText(res), ScopeWrite) {
		t.Fatalf("want IsError naming %s, got IsError=%v text=%q", ScopeWrite, res.IsError, resultText(res))
	}
	if p.RestartCount() != 0 {
		t.Fatal("platform.Restart was called with a read-only token")
	}
}

func TestHiddenRestartAuditsVerifiedSubject(t *testing.T) {
	base, p := startServer(t)
	cs := mustConnect(t, base, "write-token")
	res, err := call(t, cs, "restart_deployment", map[string]any{
		"namespace": "shop", "name": "checkout",
		"reason": "  stuck rollout rev 41, restart after config fix  ",
	})
	if err != nil || res.IsError {
		t.Fatalf("restart failed: err=%v text=%q", err, resultText(res))
	}
	r, ok := p.LastRestart()
	if !ok || r.Actor != "bob@kestrel.dev" || r.Namespace != "shop" || r.Name != "checkout" {
		t.Fatalf("restart record = %+v, want actor bob@kestrel.dev (from the token, not from arguments)", r)
	}
	if r.Reason != "stuck rollout rev 41, restart after config fix" {
		t.Fatalf("reason = %q, want trimmed", r.Reason)
	}
}

func TestHiddenRestartGuards(t *testing.T) {
	base, p := startServer(t)
	cs := mustConnect(t, base, "write-token")
	cases := []struct {
		name string
		args map[string]any
		want string
	}{
		{"protected namespace", map[string]any{"namespace": "kube-system", "name": "coredns", "reason": "dns flaky, restart coredns pods"}, "protected"},
		{"short reason", map[string]any{"namespace": "shop", "name": "cart", "reason": "pls"}, "reason"},
		{"bad name", map[string]any{"namespace": "shop", "name": "cart;rm -rf", "reason": "restart cart after deploy"}, "name"},
		{"bad namespace", map[string]any{"namespace": "../kube-system", "name": "cart", "reason": "restart cart after deploy"}, "namespace"},
	}
	for _, c := range cases {
		res, err := call(t, cs, "restart_deployment", c.args)
		if err != nil {
			t.Errorf("%s: want a tool error (IsError), got protocol error %v", c.name, err)
			continue
		}
		if !res.IsError || !strings.Contains(strings.ToLower(resultText(res)), c.want) {
			t.Errorf("%s: IsError=%v text=%q, want IsError mentioning %q", c.name, res.IsError, resultText(res), c.want)
		}
	}
	if p.RestartCount() != 0 {
		t.Fatalf("platform.Restart called %d times despite guards", p.RestartCount())
	}
}

func TestHiddenMissingRequiredArgNeverReachesPlatform(t *testing.T) {
	base, p := startServer(t)
	cs := mustConnect(t, base, "write-token")
	res, err := call(t, cs, "restart_deployment", map[string]any{"namespace": "shop", "reason": "restart without a name given"})
	if err == nil && !res.IsError {
		t.Fatalf("missing 'name' accepted: %q", resultText(res))
	}
	if p.RestartCount() != 0 {
		t.Fatal("platform.Restart called with missing name")
	}
}

func TestHiddenNotFoundIsToolErrorWithHint(t *testing.T) {
	base, _ := startServer(t)
	cs := mustConnect(t, base, "read-token")
	res, err := call(t, cs, "get_rollout_status", map[string]any{"namespace": "shop", "name": "payments"})
	if err != nil {
		t.Fatalf("not found should be a tool error, got protocol error %v", err)
	}
	if !res.IsError || !strings.Contains(resultText(res), "not found") {
		t.Fatalf("IsError=%v text=%q", res.IsError, resultText(res))
	}
}

func TestHiddenListDeploymentsStructuredAndEmpty(t *testing.T) {
	base, _ := startServer(t)
	cs := mustConnect(t, base, "read-token")
	res, err := call(t, cs, "list_deployments", map[string]any{"namespace": "empty-ns"})
	if err != nil || res.IsError {
		t.Fatalf("err=%v text=%q", err, resultText(res))
	}
	b, _ := json.Marshal(res.StructuredContent)
	if !strings.Contains(string(b), `"deployments":[]`) {
		t.Fatalf("structured content = %s, want {\"deployments\":[]} (an empty list, not null)", b)
	}
	res, err = call(t, cs, "list_deployments", map[string]any{"namespace": "Shop!"})
	if err != nil || !res.IsError {
		t.Fatalf("invalid namespace should be IsError: err=%v", err)
	}
}

func TestHiddenSessionBoundToUser(t *testing.T) {
	// Session hijacking: a valid token for another user must not be able to
	// drive alice's session by replaying her Mcp-Session-Id.
	base, _ := startServer(t)
	cs := mustConnect(t, base, "read-token")
	sid := cs.ID()
	if sid == "" {
		t.Fatal("expected a stateful session id")
	}
	body := `{"jsonrpc":"2.0","id":7,"method":"tools/list","params":{}}`
	if resp := rawPost(t, base+"/mcp", "Bearer read-token", sid, body); resp.StatusCode != 200 {
		t.Fatalf("owner request status = %d, want 200", resp.StatusCode)
	}
	resp := rawPost(t, base+"/mcp", "Bearer read-token2", sid, body)
	if resp.StatusCode != http.StatusForbidden && resp.StatusCode != http.StatusNotFound {
		t.Fatalf("another user's token on alice's session got status %d, want 403/404", resp.StatusCode)
	}
}
