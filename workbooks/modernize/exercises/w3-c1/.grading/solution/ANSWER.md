# ANSWER: modernize/w3-c1 LDAP groups to JWT claims

## Approach

Read LdapRoleResolver first to list what it really does: direct groups, nested groups (it walks
member-of-group), unknown groups ignored, disabled accounts denied. Wrote the parity matrix (users x
actions x boundary amounts) before the resolver, then made it pass.

## Fix

Validation with Nimbus: RS256 pinned by the key selector (header alg is not trusted, so none and HS256
fail), keys only from the JWKS by kid, exact iss and aud, exp/iat/sub required, 60 s skew; every failure
becomes InvalidTokenException. Mapping table from the five APP_ClaimDesk_ groups; SeniorAdjusters
implies SENIOR_ADJUSTER and ADJUSTER because Okta does not expand nested groups. Unknown groups and a
missing claim give no roles. groups may be an array or a string; names match exactly.

Gaps: nested groups (closed in the mapping); disabled accounts (Okta stops issuing, but a token lives
until exp, so access tokens are 15 minutes and deprovisioning revokes sessions); freshness in general;
the groups claim filter must keep the APP_ClaimDesk_ prefix.

## Trade-offs / what I would do in production

Shadow mode first: resolve both, log any decision difference with user and action (not the token),
enforce LDAP. When a week shows zero diffs, enforce JWT behind a flag, with LDAP kept one release as
rollback. Cache the JWKS with refresh on unknown kid for key rotation.
