# Rubric: awsfde/w4-t1 After the SPA moved to access tokens, other tenants see Acme's shipments
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: the pool's pre token generation trigger is LambdaVersion V1_0, which customizes only the ID token; custom attributes are also only in the ID token; the SPA switched to access tokens on 2026-11-12, so access tokens carry neither tenant_id nor custom:tenant_id; the resolver's fallback chain ends at DEFAULT_TENANT=acme-foods from the pilot, so every caller resolves to Acme. Acme looks fine because the default is their tenant. Partial (10-15): "the access token has no tenant claim" without the V1_0 mechanism or without the default fallback. Zero: blames SAML/federation. |
| 3 | Evidence | 20 | Full: authorizer.log claim lists (no tenant_id, token_use access, event_version 1), lambda.log "source": "env:DEFAULT_TENANT" for every request, config/user-pool.json LambdaVersion V1_0, the frontend diff, the decoded tokens, and the docs statement (V1_0 customizes the ID token; V2_0 customizes both and needs Essentials or Plus). Partial: one or two sources. |
| 4 | Red herring handled | 5 | Rules out BH-CHG-2231: test sign-in succeeded, attribute mapping unchanged, ID token still carries the right custom:tenant_id, and Corvid (OIDC) and Delta (native) are affected too. |
| 5 | Fix quality | 10 | Full: LambdaVersion V2_0 (tier is Essentials), claimsAndScopeOverrideDetails with idTokenGeneration and accessTokenGeneration, resolver reads only tenant_id and fails closed, DEFAULT_TENANT removed, frontend change kept. Partial: one of the three layers. Zero: reverts the SPA to ID tokens as the fix. |
| 6 | Exposure statement, rollout and prevention | 10 | Full: since the 08:05 ET SPA deploy, every non-Acme user who loaded shipments saw Acme Foods data (Acme is the affected data owner; no other tenant's data was exposed); rollout order: deploy the trigger that handles both event versions, then switch the pool to V2_0, then remove the fallback (or accept 403s briefly, never the default); prevention: cross-tenant tests that run with both token types, alarm on any resolution source other than the claim, ban default tenants in review. Partial: generic. |
Total: 100
