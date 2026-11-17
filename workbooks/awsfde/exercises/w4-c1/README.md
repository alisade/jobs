# awsfde/w4-c1 - Tenant-scoped tool Lambda, single-table DynamoDB and LeadingKeys

**Type:** coding | **Estimate:** 2.5 hours | **Study plan:** Week 4 (Mon: Cognito user pools; Tue: pre token generation and tenant claims; Wed: JWT authorizers; Thu: ABAC and LeadingKeys; Fri: DynamoDB single-table design)

## Scenario

Tidewater Ask's agent gets a new tool: look up a customer's support tickets. The same Lambda serves
the web app (`GET /tickets...` through an API Gateway HTTP API with a Cognito JWT authorizer) and
the agent's tool layer (`POST /tools/get_ticket`, whose body is whatever arguments the model chose).
Brightline Health's security team will run a penetration test before they enable the agent, and
they have told you exactly what they will try: forge the tenant in the path, in the body, and
through a prompt-injected tool argument.

Your deliverable is the tenant boundary at every layer: the claim in the token, the Lambda that
reads it, the table keys that make cross-tenant reads structurally hard, and the IAM policy that
stops them even if application code is wrong.

## What you have

| Path | What it is |
|---|---|
| `tickets/keys.py` | key helpers for table `tidewater-ops`; the access patterns are in the docstring - **partly yours** |
| `tickets/pretoken.py` | the Cognito pre token generation trigger - **yours** |
| `tickets/handler.py` | the HTTP API (payload 2.0) Lambda - **yours** |
| `tickets/policy.py` | the tool role's IAM policy and the session-tag assume-role helper - **yours** |
| `tests/w4c1_support.py` | a moto table with `gsi1` and `gsi2`, seed data for two tenants, event builders |

## Your task

1. **Keys (`keys.py`).** Implement the access patterns in the docstring:
   AP1 get a ticket (`pk=TENANT#<t>`, `sk=TICKET#<id>`), AP2 a tenant's tickets by status newest
   first (`gsi1`), AP3 a tenant's tickets for a shipment (`gsi2`), AP4 user to tenant mapping. Every
   partition key, on the table and on both indexes, starts with the tenant prefix. Validate ids
   (`ValueError` on anything that is not a ticket id or a lowercase tenant slug).
2. **Pre token generation (`pretoken.py`).** Event version V2_0 only. Look up the user's tenant
   (AP4) and add `tenant_id` to both `idTokenGeneration` and `accessTokenGeneration` under
   `response.claimsAndScopeOverrideDetails`. An unmapped user raises (Cognito then fails the sign-in),
   and a client-writable attribute such as `custom:tenant_id` is never trusted.
3. **Handler (`handler.py`).** Tenant from `requestContext.authorizer.jwt.claims.tenant_id` only;
   403 without it. Tenant values in the path, query string or body are never used; log them as a
   security signal. Another tenant's ticket is a 404 (not 403: do not confirm it exists). Bad ids,
   bad status or a non-JSON body are 400. Responses never include key attributes or `tenant_id`, and
   carry `cache-control: no-store`.
4. **IAM (`policy.py`).** `tool_role_policy(table_arn)`: least-privilege read access whose every
   partition key must match `TENANT#${aws:PrincipalTag/tenant_id}` (or that prefix plus `#...` for
   the indexes) through `dynamodb:LeadingKeys`. Choose the condition operator and the action list
   carefully: one common action makes the condition meaningless. `tenant_session()` assumes the role
   with a `tenant_id` session tag.
5. Fill in `ANSWER.md`.

## Acceptance criteria (what the grader checks)

- The three attacks (forged path, forged body, prompt-injected tool argument) and a forged query
  string all fail; forged tenants are logged.
- No tenant claim is a 403; another tenant's ticket is a 404; bad input is a 400; responses leak no keys.
- Items support AP1-AP3 with tenant-prefixed partition keys on the table and both GSIs.
- The trigger adds the claim to both tokens, rejects V1 events and unmapped users, and ignores
  client-supplied attributes.
- The policy uses `ForAllValues` with `dynamodb:LeadingKeys` and the session tag, has no `Scan`, no
  writes, no wildcards in actions; `tenant_session` passes the session tag.
- `ANSWER.md` explains where each layer would catch a bug in the layer above it.

## How to run

```bash
make setup
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade awsfde/w4-c1
make clean
```
