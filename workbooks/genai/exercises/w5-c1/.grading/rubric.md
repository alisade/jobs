# Rubric: genai/w5-c1 Service boundaries for the shopping assistant: three ADRs
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 0 | Does not apply: review-only design exercise (grade.sh reports 0/0) |
| 2 | ADR-1 boundaries and data ownership | 20 | Full: separate service justified by load shape (long-lived I/O-bound streams), release cadence and team ownership; catalog and orders via their APIs with the user's identity (not their databases, citing INC-2026-0903); off the storefront render/checkout path (INC-2025-1128); names the new endpoints needed and the orders change window; honest about the extra hops and operating cost; monolith-first applied to the assistant's internals. Partial: decision without the incident and ownership reasoning. Zero: reads catalog-db or orders-db directly, or puts the assistant in the SSR path. |
| 3 | ADR-2 streaming transport | 20 | Full: SSE over POST chosen for one-way streaming; concrete Kong (`response_buffering` off, timeouts) and CDN (no cache, no buffering, read timeout) changes; keepalives below idle timeouts; reconnect behaviour (Last-Event-ID resume or restart, never append); rejects WebSocket (CDN tier, no bidirectional need) and polling (request volume at peak) with numbers. Partial: picks SSE without the path changes. |
| 4 | ADR-3 fallback and rate limiting | 20 | Full: bounded retries on retryable errors only with backoff and jitter, one fallback with its own evaluated prompt, per-workload keys (INC-2026-0614), per-user and per-workload limits, per-conversation budget, metering with OTel; a reasoned choice between library and shared gateway with a revisit trigger (second consumer, central audit). Partial: "add retries and a fallback". |
| 5 | Failure modes and budgets | 20 | Failure table with blast radius, detection, user experience and mitigation for provider outage, 429s, slow catalog, orders down, assistant down, peak, bad prompt change, cost runaway; a TTFT and cost-per-conversation estimate that ties to the targets. Partial: a list without detection or user experience. |
| 6 | Clarity and ANSWER.md | 20 | Diagram that shows sync vs streaming and ownership; decisions stated first, then reasons; rejected options recorded; open questions to other teams; ANSWER.md summarizes 3-5 decisions and trade-offs. |
Total: 100
