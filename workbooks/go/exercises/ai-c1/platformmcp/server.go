// Package platformmcp is Kestrel's platform MCP server: read-only deployment
// tools plus one guarded write tool, served over streamable HTTP behind OAuth
// bearer-token auth. See README.md for the requirements.
package platformmcp

import (
	"context"
	"errors"
	"net/http"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"
	// Useful SDK packages for this exercise (read their docs):
	_ "github.com/modelcontextprotocol/go-sdk/auth"    // RequireBearerToken, TokenVerifier, TokenInfo, ProtectedResourceMetadataHandler
	_ "github.com/modelcontextprotocol/go-sdk/oauthex" // ProtectedResourceMetadata
)

// Scopes.
const (
	ScopeRead  = "platform:read"
	ScopeWrite = "platform:write" // implies ScopeRead
)

// MetadataPath is where the protected resource metadata (RFC 9728) is served.
const MetadataPath = "/.well-known/oauth-protected-resource"

// Claims are what a verified access token says. The real Verifier checks the
// JWT signature against the IdP's JWKS; tests inject a fake.
type Claims struct {
	Subject  string
	Audience []string
	Scopes   []string
	Expiry   time.Time
}

// ErrInvalidToken: the token is malformed, unsigned, revoked or unknown.
var ErrInvalidToken = errors.New("invalid token")

// Verifier validates a raw bearer token. It returns an error wrapping
// ErrInvalidToken for bad tokens, and any other error when it cannot decide
// (for example the JWKS endpoint is down).
type Verifier interface {
	Verify(ctx context.Context, token string) (*Claims, error)
}

// Config for the server.
type Config struct {
	// ResourceURL is the canonical URI of this MCP server, e.g.
	// "https://mcp.kestrel.dev/mcp". Tokens must list it in their audience.
	ResourceURL string
	// MetadataURL is the public URL of MetadataPath, returned in WWW-Authenticate.
	MetadataURL string
	// AuthorizationServers are the issuer URLs advertised in the metadata.
	AuthorizationServers []string
	// ProtectedNamespaces cannot be restarted through MCP even with platform:write.
	// Default: kube-system, istio-system.
	ProtectedNamespaces []string
}

// NewHandler returns the full HTTP handler: the unauthenticated metadata
// endpoint at MetadataPath and the authenticated MCP endpoint at /mcp.
//
// TODO (README "Requirements" 1-6):
//   - serve RFC 9728 protected resource metadata at MetadataPath
//   - wrap mcp.NewStreamableHTTPHandler in bearer-token auth: 401 + WWW-Authenticate
//     with resource_metadata for missing/invalid/expired/wrong-audience tokens,
//     403 without platform:read, 5xx when the verifier cannot decide
//   - make the verified identity and scopes visible to tool handlers
//     (req.Extra.TokenInfo) and bind sessions to the user
func NewHandler(p Platform, v Verifier, cfg Config) http.Handler {
	_ = v
	mux := http.NewServeMux()
	mux.Handle("/mcp", mcp.NewStreamableHTTPHandler(func(*http.Request) *mcp.Server { return NewServer(p, cfg) }, nil))
	return mux
}

// NewServer registers the three tools.
//
// TODO (README "Requirements" 7-11): list_deployments, get_rollout_status,
// restart_deployment with typed inputs (mcp.AddTool), per-call scope checks from
// the verified token, input validation, protected namespaces, audit actor, and
// tool errors (IsError results) instead of protocol errors for anything the
// model can recover from.
func NewServer(p Platform, cfg Config) *mcp.Server {
	_ = p
	_ = cfg
	_ = context.Background
	return mcp.NewServer(&mcp.Implementation{Name: "kestrel-platform", Version: "0.1.0"}, nil)
}
