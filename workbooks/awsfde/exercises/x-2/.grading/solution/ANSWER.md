# ANSWER: awsfde/x-2 Tenant-isolation kit

## Approach

Read the three notes for what they share rather than what differs, then the constraints: 14 teams in
two languages, three platform engineers, a slow AppSec review. That ruled out a platform service and
pointed at libraries, a CDK construct and tests.

## Fix

- The tenant comes only from verified claims, through one library in TS and Python.
- Retrieve only through a wrapper that always injects the tenant filter.
- Tool Lambdas through a construct with session-tag ABAC and LeadingKeys, no Scan.
- Authenticated API paths never cached: no-store default plus a CDN helper with a synth check.
- A cross-tenant attack suite in every service's CI replaces most of the manual AppSec checklist.
- Rollout by risk over a quarter, IAM layer first for teams that cannot adopt code yet.

## Trade-offs / what I would do in production

Left out per-user authorization and silo accounts. First spike: assume-role latency and credential
caching. Main risk: shared-library blast radius, mitigated by a small surface, its own tests and
versioned releases.
