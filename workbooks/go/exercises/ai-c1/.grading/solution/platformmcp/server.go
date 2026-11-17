// Package platformmcp is Kestrel's platform MCP server: read-only deployment
// tools plus one guarded write tool, served over streamable HTTP behind OAuth
// bearer-token auth. See README.md for the requirements.
package platformmcp

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"regexp"
	"slices"
	"strings"
	"time"
	"unicode/utf8"

	"github.com/modelcontextprotocol/go-sdk/auth"
	"github.com/modelcontextprotocol/go-sdk/mcp"
	"github.com/modelcontextprotocol/go-sdk/oauthex"
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
func NewHandler(p Platform, v Verifier, cfg Config) http.Handler {
	mux := http.NewServeMux()
	mux.Handle("GET "+MetadataPath, auth.ProtectedResourceMetadataHandler(&oauthex.ProtectedResourceMetadata{
		Resource:               cfg.ResourceURL,
		AuthorizationServers:   cfg.AuthorizationServers,
		ScopesSupported:        []string{ScopeRead, ScopeWrite},
		BearerMethodsSupported: []string{"header"},
	}))

	srv := NewServer(p, cfg)
	mcpHandler := mcp.NewStreamableHTTPHandler(func(*http.Request) *mcp.Server { return srv }, nil)
	requireToken := auth.RequireBearerToken(tokenVerifier(v, cfg.ResourceURL), &auth.RequireBearerTokenOptions{
		ResourceMetadataURL: cfg.MetadataURL,
		Scopes:              []string{ScopeRead},
	})
	mux.Handle("/mcp", requireToken(mcpHandler))
	return mux
}

// tokenVerifier adapts Verifier to the SDK: audience check (no token
// passthrough: only tokens minted for this resource), write implies read, and
// UserID set so the SDK binds sessions to the user.
func tokenVerifier(v Verifier, resource string) auth.TokenVerifier {
	return func(ctx context.Context, token string, _ *http.Request) (*auth.TokenInfo, error) {
		c, err := v.Verify(ctx, token)
		if err != nil {
			if errors.Is(err, ErrInvalidToken) {
				return nil, fmt.Errorf("%w: %v", auth.ErrInvalidToken, err)
			}
			return nil, fmt.Errorf("token verification unavailable: %w", err)
		}
		if c == nil || c.Subject == "" {
			return nil, fmt.Errorf("%w: no subject", auth.ErrInvalidToken)
		}
		if !slices.Contains(c.Audience, resource) {
			return nil, fmt.Errorf("%w: audience %v does not include %s", auth.ErrInvalidToken, c.Audience, resource)
		}
		scopes := slices.Clone(c.Scopes)
		if slices.Contains(scopes, ScopeWrite) && !slices.Contains(scopes, ScopeRead) {
			scopes = append(scopes, ScopeRead)
		}
		return &auth.TokenInfo{Scopes: scopes, Expiration: c.Expiry, UserID: c.Subject}, nil
	}
}

// ---- tools ----------------------------------------------------------------

type listIn struct {
	Namespace string `json:"namespace" jsonschema:"Kubernetes namespace"`
}
type listOut struct {
	Deployments []Deployment `json:"deployments"`
}
type statusIn struct {
	Namespace string `json:"namespace" jsonschema:"Kubernetes namespace"`
	Name      string `json:"name" jsonschema:"Deployment name"`
}
type restartIn struct {
	Namespace string `json:"namespace" jsonschema:"Kubernetes namespace"`
	Name      string `json:"name" jsonschema:"Deployment name"`
	Reason    string `json:"reason" jsonschema:"Why the restart is needed; recorded in the audit log (10-500 chars)"`
}
type restartOut struct {
	Status string `json:"status"`
}

var dns1123 = regexp.MustCompile(`^[a-z0-9]([-a-z0-9]*[a-z0-9])?$`)

func validName(field, v string) error {
	if len(v) > 63 || !dns1123.MatchString(v) {
		return fmt.Errorf("invalid %s %q: must be a DNS-1123 label", field, v)
	}
	return nil
}

// toolError is returned from typed handlers; the SDK turns it into a
// CallToolResult with IsError set, which the model can read and act on.
func toolError(format string, a ...any) error { return fmt.Errorf(format, a...) }

func hasScope(req *mcp.CallToolRequest, scope string) bool {
	if req == nil || req.Extra == nil || req.Extra.TokenInfo == nil {
		return false
	}
	return slices.Contains(req.Extra.TokenInfo.Scopes, scope)
}

func subject(req *mcp.CallToolRequest) string {
	if req == nil || req.Extra == nil || req.Extra.TokenInfo == nil {
		return ""
	}
	return req.Extra.TokenInfo.UserID
}

// NewServer registers the three tools. Every tool checks scopes from the
// verified token itself: the model's arguments can never grant access.
func NewServer(p Platform, cfg Config) *mcp.Server {
	protected := cfg.ProtectedNamespaces
	if protected == nil {
		protected = []string{"kube-system", "istio-system"}
	}
	s := mcp.NewServer(&mcp.Implementation{Name: "kestrel-platform", Version: "0.1.0"}, nil)

	mcp.AddTool(s, &mcp.Tool{
		Name:        "list_deployments",
		Description: "List Deployments in a namespace with image and ready/desired replicas. Read-only. Requires platform:read.",
	}, func(ctx context.Context, req *mcp.CallToolRequest, in listIn) (*mcp.CallToolResult, listOut, error) {
		if !hasScope(req, ScopeRead) {
			return nil, listOut{}, toolError("forbidden: list_deployments requires scope %s", ScopeRead)
		}
		if err := validName("namespace", in.Namespace); err != nil {
			return nil, listOut{}, err
		}
		deps, err := p.ListDeployments(ctx, in.Namespace)
		if err != nil {
			return nil, listOut{}, toolError("list deployments: %v", err)
		}
		if deps == nil {
			deps = []Deployment{}
		}
		return nil, listOut{Deployments: deps}, nil
	})

	mcp.AddTool(s, &mcp.Tool{
		Name:        "get_rollout_status",
		Description: "Status of the latest rollout of one Deployment (Complete, Progressing, Failed) with the controller message. Read-only. Requires platform:read.",
	}, func(ctx context.Context, req *mcp.CallToolRequest, in statusIn) (*mcp.CallToolResult, Rollout, error) {
		if !hasScope(req, ScopeRead) {
			return nil, Rollout{}, toolError("forbidden: get_rollout_status requires scope %s", ScopeRead)
		}
		if err := errors.Join(validName("namespace", in.Namespace), validName("name", in.Name)); err != nil {
			return nil, Rollout{}, err
		}
		r, err := p.RolloutStatus(ctx, in.Namespace, in.Name)
		if errors.Is(err, ErrNotFound) {
			return nil, Rollout{}, toolError("deployment %s/%s not found; call list_deployments to see what exists", in.Namespace, in.Name)
		}
		if err != nil {
			return nil, Rollout{}, toolError("rollout status: %v", err)
		}
		return nil, r, nil
	})

	mcp.AddTool(s, &mcp.Tool{
		Name:        "restart_deployment",
		Description: "Trigger a rolling restart of one Deployment. Mutating. Requires platform:write. Not allowed in protected namespaces. Give a reason; it is audited.",
	}, func(ctx context.Context, req *mcp.CallToolRequest, in restartIn) (*mcp.CallToolResult, restartOut, error) {
		if !hasScope(req, ScopeWrite) {
			return nil, restartOut{}, toolError("forbidden: restart_deployment requires scope %s; this token is read-only", ScopeWrite)
		}
		if err := errors.Join(validName("namespace", in.Namespace), validName("name", in.Name)); err != nil {
			return nil, restartOut{}, err
		}
		if n := utf8.RuneCountInString(strings.TrimSpace(in.Reason)); n < 10 || n > 500 {
			return nil, restartOut{}, toolError("reason must be 10-500 characters describing why the restart is needed")
		}
		if slices.Contains(protected, in.Namespace) {
			return nil, restartOut{}, toolError("forbidden: namespace %s is protected; restarts there need a human change request", in.Namespace)
		}
		err := p.Restart(ctx, in.Namespace, in.Name, subject(req), strings.TrimSpace(in.Reason))
		if errors.Is(err, ErrNotFound) {
			return nil, restartOut{}, toolError("deployment %s/%s not found", in.Namespace, in.Name)
		}
		if err != nil {
			return nil, restartOut{}, toolError("restart: %v", err)
		}
		return nil, restartOut{Status: fmt.Sprintf("restart of %s/%s requested", in.Namespace, in.Name)}, nil
	})
	return s
}
