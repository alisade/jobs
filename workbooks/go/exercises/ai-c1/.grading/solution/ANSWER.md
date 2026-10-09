# go/ai-c1 ANSWER (model)

## Approach

Read the go-sdk `auth` package and the streamable transport first and found that
`auth.RequireBearerToken` stores `TokenInfo` under a private context key the transport
reads for `req.Extra.TokenInfo` and session binding, so I adapted my `Verifier` to
`auth.TokenVerifier` instead of writing my own middleware. Tested with the go-sdk client
for tool behaviour and raw `http.Post` for status codes and challenges.

## Fix

- Metadata at `/.well-known/oauth-protected-resource` via `ProtectedResourceMetadataHandler`.
- Adapter: `ErrInvalidToken` -> `auth.ErrInvalidToken` (401), other errors -> 500,
  audience must contain `ResourceURL`, write implies read, `UserID = Subject`.
- `RequireBearerToken` with `Scopes: [platform:read]` and the metadata URL.
- Three typed tools; each checks scope from `req.Extra.TokenInfo`, validates DNS-1123
  names, reason length and protected namespaces before touching the platform; errors are
  returned as tool errors with actionable text.

## Trade-offs / what I would do in production

- List all tools, enforce at call time: stable tool list, explainable denials.
- Real verifier with cached JWKS, issuer and audience checks, small clock skew.
- Restart behind human confirmation; per-subject rate limits; audit to a durable store.
- Istio RequestAuthentication + AuthorizationPolicy in front as defence in depth.
