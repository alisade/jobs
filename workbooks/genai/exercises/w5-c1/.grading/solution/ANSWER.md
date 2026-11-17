# ANSWER: genai/w5-c1 Service boundaries for the shopping assistant

## Approach

I read the incident history first. It explains most of the constraints: the Black Friday brownout rules
out a synchronous dependency in the storefront, the vendor outage asks for backoff, fallback and
workload keys, and the schema-change incident rules out reading other teams' databases. I then weighed
each ADR against the peak numbers (3,600 concurrent streams), the cost ceiling and the team sizes.

## Fix

DESIGN.md has three ADRs, a system diagram, a failure table and a latency/cost budget. Key decisions:

1. The assistant is a separate service owned by the AI team, loaded client-side behind a flag. It is
   never on the storefront render or checkout path.
2. Catalog and orders are reached through their APIs, with the user's token forwarded. The assistant
   needs two new endpoints (batch stock, associate-scoped orders), and I planned the orders one
   around the Q4 change window.
3. Streaming is SSE over POST through the existing CDN and Kong, with buffering off, longer timeouts,
   keepalives and event ids. I rejected WebSocket (cost, no need) and polling (request volume at
   peak).
4. Model resilience lives in an in-process library with a provider-neutral interface. It does bounded
   retries with backoff, one fallback to provider B, per-workload keys and a per-conversation budget.
   It becomes a shared gateway when a second consumer appears.

## Trade-offs / what I would do in production

- An extra service and network hops buy blast-radius isolation, independent scaling and eval-gated
  releases.
- No shared LLM gateway yet: cross-team quotas are not central until we extract one.
- SSE depends on every intermediary not buffering. I would prove that first with a fake-model prototype
  through the real CDN path, plus a synthetic TTFT probe.
- I would revisit ADR-3 when the catalog team's enrichment workload goes to production.
