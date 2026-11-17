# Reference: genai/w5-c1

Model answer: `.grading/solution/DESIGN.md`.

What great looks like:
- ADR-1: the assistant is a separate service because its load shape (thousands of long streams, I/O
  bound), cadence (eval-gated prompt changes) and failure modes differ from the storefront. It is kept
  off the render and checkout path (INC-2025-1128), and it uses catalog and order APIs with the user's
  token (INC-2026-0903, least privilege). It names the new endpoints it needs and the Q4 orders window.
  Internals stay a modular monolith.
- ADR-2: SSE over POST through the existing CDN and Kong with buffering off, timeouts raised,
  keepalives under the shortest idle timeout, and event ids for resume. WebSocket is rejected (CDN tier,
  no need for bidirectional traffic) and so is polling (about 10k rps of empty polls at peak).
- ADR-3: an in-process resilience library now, with a provider-neutral interface, per-workload keys,
  bounded retries, one fallback, a budget guard and OTel metering. A shared gateway comes when a second
  consumer or central audit appears. A candidate who picks the gateway can still score full marks if
  they own its operations, latency and SPOF cost and say who runs it in Q4 when platform said no.
- A failure table and budgets that show operational thinking.

Common misses: reading catalog-db for speed, forgetting the CDN buffers responses, retries without a
budget, no answer for "who is on call for the gateway", ignoring the orders change freeze.
