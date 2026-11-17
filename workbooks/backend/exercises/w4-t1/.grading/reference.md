# Reference: backend/w4-t1

Injected fault: `src/context.ts` builds one DataLoader at module scope and a module-level `currentAuth`
(KEY-2410). Fix: `.grading/solution/src/context.ts` creates loaders per request with the auth captured.

DataLoader is designed as a per-request memo plus a batching window (one tick of the event loop). Its
cache has no TTL and no notion of who asked. Shared across requests it becomes an unbounded,
identity-blind cache: rows loaded for one tenant are served to another when ids collide (they do here,
because CRM-migrated ids are unique per tenant), and nothing is ever invalidated (stale rename until a
restart). The batch function also ran with whichever request last set `currentAuth`, so concurrent
requests could send each other's ids under the wrong token; accounts-svc then correctly returned
not-found or the caller's own row for those ids, which produced null accounts and swapped names.

Why the red herring fails: POST /graphql is never cached by the CDN and responses are `private,
no-store`. "A refresh fixes it" is explained by process-local state that depends on request order.

Interview angles: "Where does authorization belong in GraphQL?" (in the data layer the loaders call,
with the request's identity, not in the resolver tree only). "When is a cross-request cache OK?" (a real
cache keyed by tenant and permission scope with invalidation, e.g. on account-updated events). "How do
you test it?" (interleaved requests from two tenants with colliding ids).
