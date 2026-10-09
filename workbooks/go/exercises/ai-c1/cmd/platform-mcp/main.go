// Command platform-mcp serves the Kestrel platform MCP server on :8080 with the
// in-memory fake platform and a demo verifier that accepts two static tokens.
// For local poking with MCP Inspector only; production wires a JWKS verifier.
package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/kestrel-platform/platform-mcp/platformmcp"
)

type demoVerifier struct{}

func (demoVerifier) Verify(_ context.Context, token string) (*platformmcp.Claims, error) {
	aud := []string{"http://localhost:8080/mcp"}
	exp := time.Now().Add(time.Hour)
	switch token {
	case "demo-read":
		return &platformmcp.Claims{Subject: "demo-reader", Audience: aud, Scopes: []string{platformmcp.ScopeRead}, Expiry: exp}, nil
	case "demo-write":
		return &platformmcp.Claims{Subject: "demo-writer", Audience: aud, Scopes: []string{platformmcp.ScopeWrite}, Expiry: exp}, nil
	}
	return nil, fmt.Errorf("unknown demo token: %w", platformmcp.ErrInvalidToken)
}

func main() {
	h := platformmcp.NewHandler(platformmcp.NewFakePlatform(), demoVerifier{}, platformmcp.Config{
		ResourceURL:          "http://localhost:8080/mcp",
		MetadataURL:          "http://localhost:8080" + platformmcp.MetadataPath,
		AuthorizationServers: []string{"https://idp.example.invalid"},
	})
	log.Println("listening on http://localhost:8080/mcp (tokens: demo-read, demo-write)")
	srv := &http.Server{Addr: "localhost:8080", Handler: h, ReadHeaderTimeout: 5 * time.Second}
	log.Fatal(srv.ListenAndServe())
}
