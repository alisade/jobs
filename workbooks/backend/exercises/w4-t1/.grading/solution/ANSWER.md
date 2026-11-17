# ANSWER: backend/w4-t1 Sales managers see someone else's account names in the pipeline view

## Approach

Read the ticket and the git log first: symptoms started with the sprint 44 deploy (KEY-2410, DataLoader
for Opportunity.account). Edge team evidence rules out the CDN: POST /graphql is pass-through and the
response has `cache-control: private, no-store`. Reproduced with `make repro`: an EMEA request followed
by an AMER request on the same process shows `Fjordline AS` on the AMER deal.

## Root cause

`src/context.ts` creates one DataLoader for the whole process (module scope) and sets a module-level
`currentAuth` per request. That breaks two DataLoader assumptions:

1. The loader cache is a per-request memo keyed only by account id. Account ids are unique per tenant
   only, so after an EMEA request cached `1042 -> Fjordline AS`, an AMER request for its own `1042` got
   the cached EMEA row (repro: `bu-amer u-dana sees ["Fjordline AS","Harbor Labs"]`, and only `1044` was
   fetched for bu-amer). The cache also never expires, which is the stale rename until a pod restart.
2. The batch function reads `currentAuth` when the batch runs, which is whichever request called
   `createContext` last. Interleaved requests send one request's ids under another's token:
   query-log.txt `r-71a4 batchGet?ids=1042,1043 tenant=bu-amer` (1043 is EMEA's id, from r-71a3) and
   `r-71ca batchGet?ids=2001...2020 tenant=bu-emea` returning not-found for AMER's accounts.

"A refresh fixes it" fits: the result depends on which requests shared the process and in what order,
and pods differ (x2k4q vs b8m1z).

## Fix

Loaders are created per request in `createContext` (`createLoaders(store, auth)`), with the auth captured
in the batch function's closure. Verified: the interleaved and sequential two-tenant tests pass, each
accounts-svc call carries the right tenant, a rename shows on the next request, and there is still one
batch call per request.

## Trade-offs / what I would do in production

- Rule and test: loaders only in the context factory; a test that runs two tenants interleaved.
- Cross-request caching only in a real cache with the tenant (and permission scope) in the key and an
  invalidation story, never in DataLoader.
- Security: treat as a cross-tenant disclosure since 2026-11-03; scope affected requests from the query
  log (batch calls whose tenant differs from the request's), including agent assistant transcripts.
