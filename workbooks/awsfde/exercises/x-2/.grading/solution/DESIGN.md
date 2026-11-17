# Design: a reusable tenant-isolation kit for Tidewater Ask services

Author: FDE team   Status: proposal   Date: 2026-11-13

## 1. The pattern behind the three incidents

In all three incidents the tenant boundary was an optional decision made per call in application
code: a fallback that dropped the Retrieve filter, a tool that preferred a model-supplied argument
over the verified claim, and a response that did not say "do not cache". In each case there was no
second layer below the code (IAM, a mandatory data filter, an edge default) and no test that tried to
cross tenants. Each fix was local to one repo, so the same class of bug survived in other services.

## 2. Goals and non-goals

Goals: every tenant-data path in the 14 services uses the kit within one quarter; adoption costs a
team under one day per service; AppSec review for a kit-compliant change drops from up to a week to
one day; every service runs the cross-tenant attack suite in CI; we can hand customers an isolation
evidence pack. Non-goals: a new platform service, per-tenant accounts (silo) for everyone, fine-grained
per-user authorization (later, with Verified Permissions).

## 3. The kit: components

| Component | Form | Guarantee |
|---|---|---|
| `tenant-context` | library, TS and Python | The only way to obtain a tenant: from verified JWT claims (HTTP API authorizer context or AgentCore Gateway inbound auth). Fails closed. No API accepts a tenant string from a request. |
| `scoped-retrieve` | library | Wraps bedrock-agent-runtime Retrieve; always injects `equals tenant_id`, ANDs user filters, rejects filters on tenant_id, drops and alarms on foreign chunks. There is no unfiltered call. |
| `TenantScopedTool` | CDK construct (TS, published to Python via jsii) | Lambda + role assumed with a `tenant_id` session tag; DynamoDB access with `ForAllValues:StringLike dynamodb:LeadingKeys` on `TENANT#${aws:PrincipalTag/tenant_id}*`, no Scan; S3 prefix condition; AgentCore Gateway Lambda target via the stable `aws-cdk-lib/aws-bedrockagentcore` constructs; default response headers `cache-control: no-store`. |
| `AuthenticatedApiBehavior` | CDK helper | Adds CloudFront behaviors for authenticated paths on Managed-CachingDisabled; synth fails if an authenticated path pattern maps to a caching policy. |
| `xtenant-attack-kit` | pytest plugin and jest preset | Standard attacks per tool: forged path, body, query, prompt-injected tool argument, unfiltered retrieval, cached authenticated response. Runs against the service's handler with two seeded tenants. |
| Eval cases | JSONL for the agent eval harness | Injection and cross-tenant cases that every agent release must pass. |
| Runbook | markdown | "Suspected cross-tenant exposure": logs to pull, how to scope exposure, who to notify. |

## 4. API sketch

```python
from tenant_context import tenant_from_http_event, TenantContext   # raises NoTenant -> 403
from scoped_retrieve import retrieve

def handler(event, context):
    ctx: TenantContext = tenant_from_http_event(event)              # claims only
    chunks = retrieve(kb_id=KB, ctx=ctx, query=q, user_filters=[{"equals": {"key": "doc_type", "value": "sop"}}])
    table = ctx.dynamodb_table("tidewater-ops")                     # credentials from the tagged session
    return ctx.json_response(200, {"answer": compose(chunks)})      # no-store by default
```

```typescript
const tool = new TenantScopedTool(this, 'TicketLookup', {
  entry: 'src/ticket.ts',
  table: opsTable,                      // grants GetItem/Query with LeadingKeys, never Scan
  gateway,                              // adds a Lambda target with the tool schema
  toolSchema: ticketLookupSchema,
});
new AuthenticatedApiBehavior(this, 'Api', { distribution, pathPattern: '/api/*', origin: apiOrigin });
```

## 5. Defense in depth: which layer catches which bug

| Bug | Library | IAM | Data filter | Edge | Tests/evals |
|---|---|---|---|---|---|
| Retrieve fallback without filter (Delta) | no unfiltered call exists | - | foreign-chunk drop + alarm | - | unfiltered-retrieval attack |
| Tenant from tool argument (Brightline) | no tenant parameter in API | LeadingKeys denies other tenants | - | - | forged-argument attack |
| Cached embed URL (Corvid) | no-store default | - | - | CachingDisabled helper, synth check | cached-response attack |
| Anticipated: S3 presigned URL for wrong prefix | prefix from ctx only | s3:prefix condition on tag | - | - | presign attack |

## 6. Adoption and rollout

1. Weeks 1-2: platform team ships the libraries and construct v1, migrates the three incident services
   as reference implementations, measures adoption time.
2. Weeks 3-8: services ordered by risk: retrieval and tenant-data writes first, then reads, then
   analytics. Each adoption is a normal two-week release with the attack suite added.
3. AppSec checklist becomes: kit used for every tenant-data path (synth-time check), attack suite green
   in CI, exceptions documented. Target review time one day.
4. Teams that cannot adopt in time get an exception with an owner and a date, and the IAM layer
   (LeadingKeys role) is applied first because it needs no code change.

## 7. How we know it works

CI: attack suite per service, the synth rules (no Retrieve outside the wrapper, no authenticated path
on a caching policy, no tool role with Scan). Runtime: alarms on foreign_chunk_dropped,
tenant_param_ignored and refused recipients, CloudTrail queries for AccessDenied on tenant roles.
Reporting: monthly adoption dashboard and an evidence pack (test runs, policies, alarm history) for
customer vendor reviews.

## 8. What not to generalize

Tenant-specific business rules stay in services. Admin and cross-tenant support tools stay separate
Gateway targets with their own authorizer, not a flag in the kit. Catalog-style public caching stays
per path; the kit only forbids caching authenticated responses. No generic "filter builder" for every
data store; Retrieve and DynamoDB first, others when a second user appears.

## 9. Risks and open questions

A bug in the shared library is now a bug everywhere: small surface, its own attack tests, semantic
versioning with a security channel for urgent fixes. Three platform engineers: keep scope to the table
above. Open: assume-role latency per request (cache tagged credentials per tenant for their lifetime);
whether Policy (alpha) should later enforce tool-call rules at the Gateway.

## 10. The FDE story

"Three customers in six weeks hit three different-looking cross-tenant bugs. The ask was 'fix Delta's
answers', which was a one-line fix. The real question was why it kept happening: in every case the
tenant was an optional decision in application code with nothing underneath. We turned the three
fixes into a small kit: a tenant-context library, a Retrieve wrapper, a CDK construct with ABAC and
LeadingKeys, and an attack suite. Fourteen services adopted it in a quarter, AppSec review for tenant
paths went from a week to a day, and the attack suite has since caught two regressions in CI."
