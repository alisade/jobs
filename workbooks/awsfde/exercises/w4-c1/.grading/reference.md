# Reference: awsfde/w4-c1

Solution files: `.grading/solution/tickets/*.py`.

- **Claims.** With event version V2_0 the trigger returns `claimsAndScopeOverrideDetails` with
  `idTokenGeneration` and `accessTokenGeneration`. V1_0 can only customize the ID token, which is the
  trap behind w4-t1. Unmapped users raise, so Cognito refuses to issue tokens. Never trust a
  user-writable `custom:` attribute for tenancy.
- **Handler.** One function reads `requestContext.authorizer.jwt.claims.tenant_id`. Supplied tenant
  values are logged, never used. A foreign ticket is a 404 because the key is built from the
  caller's tenant, so the item simply does not exist for them; a 403 would confirm it exists.
- **Keys.** Tenant prefix on every partition key, table and GSIs. Access patterns first, then keys.
- **IAM.** `ForAllValues:StringLike` on `dynamodb:LeadingKeys` with
  `TENANT#${aws:PrincipalTag/tenant_id}` and `TENANT#${aws:PrincipalTag/tenant_id}#*`. No Scan: a Scan
  has no leading keys and `ForAllValues` over an empty set evaluates to true, so granting Scan would
  let any tenant session read the whole table. `ForAnyValue` would be wrong too: one matching key in a
  BatchGetItem would allow the others. The role is assumed with a `tenant_id` session tag.

Production: cache the tenant session credentials per tenant for their lifetime; consider silo tables
or accounts for regulated tenants; Verified Permissions for per-user rules; run the attack tests in CI.
