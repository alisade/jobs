# Rubric: go/ai-c1 Secure platform MCP server with the official Go SDK
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Authentication layer | 15 | Full: RFC 9728 metadata, correct 401/403/5xx split with `resource_metadata` challenge, audience check in the verifier adapter, write-implies-read normalised once, subject passed as `TokenInfo.UserID` so sessions bind to the user. Partial: works but audience or 5xx-vs-401 is wrong, or a hand-rolled middleware that bypasses the SDK's TokenInfo plumbing. Zero: token presence only. |
| 3 | Server-side authorization and guards | 15 | Full: every tool checks scope from `req.Extra.TokenInfo` (not from args, not only at the HTTP layer), DNS-1123 validation, protected namespaces, reason length, audit actor from the token; checks happen before the platform call. Partial: one guard missing or checks only via tools/list filtering. Zero: relies on the model or the prompt. |
| 4 | Tool error design | 5 | Full: recoverable problems are `IsError` results with actionable text (missing scope named, hint to list_deployments); protocol errors only for protocol problems; empty list is `[]`. Partial: mixes the two. Zero: panics or opaque errors. |
| 5 | ANSWER.md and production judgement | 15 | Full: explains the layering and the list-all-enforce-on-call choice, plus 3+ concrete production points (JWKS caching and key rotation, token exchange for downstream calls instead of passthrough, human confirmation for mutating tools, per-subject rate limits, audit to a durable sink, Istio RequestAuthentication/AuthorizationPolicy as defence in depth, prompt injection via tool results). Partial: generic. Zero: empty. |
Total: 100
