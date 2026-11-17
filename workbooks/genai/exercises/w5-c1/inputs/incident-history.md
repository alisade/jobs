# Incidents that shaped the requirements

## INC-2025-1128 Black Friday storefront brownout (sev1, 2 h 10 min)

A new "recently viewed" widget in the storefront monolith called catalog-service synchronously for every
page render. At 11x traffic catalog-service's connection pool saturated; storefront threads blocked on it;
the whole storefront went down, including checkout. Postmortem actions: timeouts and circuit breakers on
every storefront dependency (done), and "no new synchronous dependency on the checkout path without a
fallback" (policy).

## INC-2026-0614 Vendor model outage during the hack-week pilot (sev3)

The internal pilot of a product-description generator called one model provider directly. The provider
had a 47-minute partial outage with HTTP 529 (overloaded) responses. The pilot's code retried each call
5 times with no backoff and hit the account's rate limit, which also blocked a second internal tool using
the same API key for another 30 minutes after the provider recovered. Lessons: one key per workload,
backoff with jitter, a fallback model, and rate limits we control.

## INC-2026-0903 Catalog schema change breaks batch jobs (sev3)

Renaming `products.list_price` to `price_cents` in catalog-db broke two batch jobs that read the table
directly. Catalog team asked that "nobody new reads our database directly".
