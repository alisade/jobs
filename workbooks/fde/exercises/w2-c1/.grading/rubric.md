# Rubric: fde/w2-c1 JWT/JWKS-authenticated streamable-HTTP MCP server
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 45 | points = 45 * passed / total from grade.sh |
| 2 | Verification correctness | 15 | Full: alg read from the header but checked against an allow-list AND the key's kty before `jwt.decode(..., algorithms=[alg])`; `audience=`, `issuer=`, `leeway=`, `options={"require": [...]}` all passed; never `verify_signature=False`, never `algorithms` taken from the token unchecked. Partial: one of these missing but covered by luck. Zero: decodes without pinning. |
| 3 | JWKS cache design | 15 | Full: TTL refresh, unknown-kid refresh with a cooldown that cannot be abused, single-flight lock (re-check after acquiring), last-good keys on outage, bad keys skipped, injectable clock used. Partial: works but refresh logic duplicated or racy. Zero: fetch per request or no refresh on unknown kid. |
| 4 | HTTP semantics | 10 | Full: RFC 6750/9728-shaped challenges (`resource_metadata`, `error`, `scope`), 401 vs 403 used correctly, reasons only in logs, body replayed correctly for the downstream app (no lost or duplicated body), batches handled. Partial: right codes, sloppy headers. |
| 5 | Identity binding | 5 | Principal set on `scope["state"]` only after verification; nothing lets a caller choose the identity. |
| 6 | ANSWER.md and trade-offs | 10 | Full: explains the cooldown threat model and the scope-in-middleware choice, plus at least one production concern with a position (DPoP or mTLS, token exchange for the Managed Agents hop, introspection for revocation, logging of `sub` vs digest). Partial: generic. Zero: empty. |
Total: 100
