# Rubric: modernize/w3-c1 LDAP groups to JWT claims
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 55 | points = 55 * passed / total from grade.sh (3 visible LDAP baseline tests already pass) |
| 2 | Validation quality | 15 | Full: algorithm pinned server-side (not taken from the header), issuer and audience exact, required exp, bounded skew, keys only from the JWKS by kid, one exception type at the boundary, no token contents logged. Partial: library defaults with no reasoning. Zero: decoding without verifying. |
| 3 | Semantic gaps found | 20 | Full: names the gaps and how each is closed: nested groups (Okta emits direct memberships, so SeniorAdjusters must imply ADJUSTER), unknown groups ignored (gus), disabled accounts (Okta deactivation stops new tokens but issued tokens live until exp: keep lifetimes short or revoke), group name drift and the claim filter, freshness (LDAP checked every request, a token is a snapshot). Partial: one or two. |
| 4 | Cutover and rollback | 10 | Full: shadow mode computing both decisions and logging diffs before enforcing JWT, a feature flag to fall back to LDAP, decision-diff dashboard, key rotation and JWKS caching noted. Partial: "test in UAT". |
Total: 100
