package platformmcp

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

const testResource = "https://mcp.kestrel.dev/mcp"
const testMetadataURL = "https://mcp.kestrel.dev/.well-known/oauth-protected-resource"

// fakeVerifier stands in for JWT validation against the IdP's JWKS.
type fakeVerifier map[string]*Claims

var errJWKSDown = errors.New("fetch https://idp.kestrel.dev/.well-known/jwks.json: dial tcp: i/o timeout")

func (f fakeVerifier) Verify(ctx context.Context, token string) (*Claims, error) {
	if token == "jwks-down" {
		return nil, errJWKSDown
	}
	c, ok := f[token]
	if !ok {
		return nil, fmt.Errorf("signature check failed: %w", ErrInvalidToken)
	}
	return c, nil
}

func testVerifier() fakeVerifier {
	soon := time.Now().Add(time.Hour)
	return fakeVerifier{
		"read-token":  {Subject: "alice@kestrel.dev", Audience: []string{testResource}, Scopes: []string{ScopeRead}, Expiry: soon},
		"read-token2": {Subject: "mallory@kestrel.dev", Audience: []string{testResource}, Scopes: []string{ScopeRead}, Expiry: soon},
		"write-token": {Subject: "bob@kestrel.dev", Audience: []string{testResource}, Scopes: []string{ScopeWrite}, Expiry: soon},
		"other-aud":   {Subject: "alice@kestrel.dev", Audience: []string{"https://grafana.kestrel.dev"}, Scopes: []string{ScopeRead, ScopeWrite}, Expiry: soon},
		"expired":     {Subject: "alice@kestrel.dev", Audience: []string{testResource}, Scopes: []string{ScopeRead}, Expiry: time.Now().Add(-time.Minute)},
		"no-scope":    {Subject: "carol@kestrel.dev", Audience: []string{testResource}, Scopes: []string{"profile"}, Expiry: soon},
	}
}

func testConfig() Config {
	return Config{
		ResourceURL:          testResource,
		MetadataURL:          testMetadataURL,
		AuthorizationServers: []string{"https://idp.kestrel.dev"},
	}
}

// startServer runs NewHandler on httptest and returns its base URL and the fake platform.
func startServer(t *testing.T) (string, *FakePlatform) {
	t.Helper()
	p := NewFakePlatform()
	srv := httptest.NewServer(NewHandler(p, testVerifier(), testConfig()))
	t.Cleanup(srv.Close)
	return srv.URL, p
}

type bearer struct {
	token string
	base  http.RoundTripper
}

func (b bearer) RoundTrip(r *http.Request) (*http.Response, error) {
	r = r.Clone(r.Context())
	if b.token != "" {
		r.Header.Set("Authorization", "Bearer "+b.token)
	}
	return b.base.RoundTrip(r)
}

// connect opens an MCP client session to base+"/mcp" presenting token.
func connect(t *testing.T, base, token string) (*mcp.ClientSession, error) {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	c := mcp.NewClient(&mcp.Implementation{Name: "triage-agent", Version: "test"}, nil)
	cs, err := c.Connect(ctx, &mcp.StreamableClientTransport{
		Endpoint:   base + "/mcp",
		HTTPClient: &http.Client{Transport: bearer{token, http.DefaultTransport}, Timeout: 10 * time.Second},
		MaxRetries: -1,
	}, nil)
	if err == nil {
		t.Cleanup(func() { _ = cs.Close() })
	}
	return cs, err
}

func mustConnect(t *testing.T, base, token string) *mcp.ClientSession {
	t.Helper()
	cs, err := connect(t, base, token)
	if err != nil {
		t.Fatalf("connect with %s: %v", token, err)
	}
	return cs
}

func call(t *testing.T, cs *mcp.ClientSession, name string, args map[string]any) (*mcp.CallToolResult, error) {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	return cs.CallTool(ctx, &mcp.CallToolParams{Name: name, Arguments: args})
}

func resultText(r *mcp.CallToolResult) string {
	s := ""
	for _, c := range r.Content {
		if tc, ok := c.(*mcp.TextContent); ok {
			s += tc.Text
		}
	}
	return s
}
