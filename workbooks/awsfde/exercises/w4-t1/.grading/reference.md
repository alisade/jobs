# Reference: awsfde/w4-t1

**Root cause.** The user pool's pre token generation trigger is configured with
`LambdaVersion: V1_0`. The Cognito docs: a V1_0 event lets you customize the ID token; V2_0 (and
V3_0) events customize both the ID and the access token and are available in the Essentials and Plus
feature plans. So `tenant_id` was only ever in ID tokens, as was the `custom:tenant_id` attribute.
Web release 2026.11.11 (deployed 2026-11-12 08:05 ET) correctly switched the SPA to access tokens.
Access tokens carry neither claim, and the resolver's pilot-era fallback chain ends in
`DEFAULT_TENANT=acme-foods`, so every request resolves to Acme Foods. Acme users see their own data,
which is why "nothing looks wrong" for them.

**Evidence.** `run/authorizer.log`: token_use access, event_version 1, no tenant claim in any
request. `run/lambda.log`: `"source": "env:DEFAULT_TENANT"` for all five users.
`config/user-pool.json`: V1_0. `evidence/tokens-decoded.md`: the claim is in the ID token only.

**Red herring.** The SAML certificate rotation: Brightline's test sign-in succeeded, the attribute
mapping is unchanged, the ID token has the right tenant, and OIDC and native users are affected the
same way.

**Fix.** Trigger handles the V2_0 event and writes `claimsAndScopeOverrideDetails` for both tokens;
pool switched to V2_0 (the pool is on Essentials); resolver reads only `tenant_id` and returns 403
otherwise; `DEFAULT_TENANT` deleted. Keep the access-token change.

**Rollout order.** Deploy the trigger code that answers both event versions, then switch the pool
to V2_0 (users must sign in again or refresh to get new tokens), and remove the fallback at the same
time or first: a 403 is an outage, a default tenant is a breach.

**Exposure.** Since 08:05 ET on 2026-11-12, Brightline, Corvid and Delta users who loaded the
shipments page saw Acme Foods shipments (ids, destinations, values). Acme is the data owner to notify.

**Prevention.** Cross-tenant tests that run with both token types, an alarm on any resolution source
other than the claim, and a review rule that bans default tenants and claim fallbacks.
