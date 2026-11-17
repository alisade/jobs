# ANSWER: awsfde/w4-t1 Other tenants see Acme's shipments

## Approach

Read the ticket, then run/summary.txt (4 of 5 users served acme-foods). lambda.log shows how the
tenant was resolved; authorizer.log shows which claims arrived. Compared with the token payloads and
the user pool config, then the SPA diff.

## Root cause

config/user-pool.json has PreTokenGenerationConfig.LambdaVersion V1_0. Per the Cognito docs a V1_0
event customizes the ID token only; V2_0 customizes ID and access tokens (Essentials or Plus).
authorizer.log: token_use access, event_version 1, claims auth_time, client_id, iss, scope, sub,
token_use, username: no tenant_id. The SPA started sending access tokens at 08:05 ET (PR #418). The
resolver falls back to custom:tenant_id (ID token only) and then DEFAULT_TENANT=acme-foods; lambda.log
shows "source": "env:DEFAULT_TENANT" for every user. Acme sees its own data, so Acme reports nothing.
The SAML rotation is unrelated: test sign-in passed, mapping unchanged, ID token correct, and OIDC
and native users are affected identically.

## Fix

Pool LambdaVersion V2_0; trigger returns claimsAndScopeOverrideDetails with tenant_id in
idTokenGeneration and accessTokenGeneration; resolver reads only tenant_id and the handler returns
403 without it; DEFAULT_TENANT removed. make replay: 5 of 5 users served their own tenant.

## Trade-offs / what I would do in production

Exposure: Brightline, Corvid and Delta users who opened shipments since 08:05 ET saw Acme Foods
shipments; notify Acme. Rollout: trigger first (handles both versions), then pool to V2_0, with the
fallback removed so a gap is a 403 not a breach. Prevention: tests with both token types, alarm on
non-claim resolution, no default tenants.
