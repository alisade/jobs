# Reference: modernize/w3-c1

`.grading/solution/src/main/java/com/corvane/claimdesk/auth/JwtRoleResolver.java` uses Nimbus
`DefaultJWTProcessor` with `JWSVerificationKeySelector(RS256, ImmutableJWKSet)` (so `none`, HS256 and
unknown keys never verify), `DefaultJWTClaimsVerifier(audience, exact iss, required exp/iat/sub)` with a
60 s skew, and wraps every failure in `InvalidTokenException`.

The parity trap: the LDAP resolver walks nested groups, so ben (claims-senior-adjusters, nested in
claims-adjusters) has ADJUSTER and SENIOR_ADJUSTER. Okta's groups claim carries direct memberships only,
so a one-to-one mapping silently drops ADJUSTER for ben. ClaimPolicy happens to check SENIOR first, so the
approval matrix is still equal, but the role sets differ and any other check of ADJUSTER would break: map
APP_ClaimDesk_SeniorAdjusters to both roles. gus has only an unmapped group and must get nothing.
Disabled accounts: LDAP denies on the next request; with tokens, deprovisioning takes effect when the
token expires unless you revoke or introspect.

Rollout: shadow mode (compute both, log diffs, enforce LDAP), then enforce JWT behind a flag, keep LDAP
for one release as rollback.
