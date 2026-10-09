# Rubric: fde/w3-c1 AgentTrustMixin: per-hook fail policy over StorefrontBackend
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 45 | points = 45 * passed / total from grade.sh |
| 2 | Native result mapping | 15 | Full: cart denial via `domain_error` -> `ToolOutcome.held("trust")`, checkout via `PresentationRefused` (gate for deny/review, no gate for fail-closed), and ANSWER.md explains why each path is the right seam (executor ladder vs presentation enrichment; same bytes on all three runtimes). Partial: works but explanation missing or mechanism accidental. Zero: new tool, prompt change, or raw exceptions reaching the model. |
| 3 | Fail policy and async correctness | 15 | Full: one assessment path; `asyncio.timeout` per hook from policy; `TimeoutError` and client exceptions handled, `CancelledError` not swallowed (no `except BaseException`, no bare `except:`); decision computed before logging; no retries that blow the budget. Partial: per-hook logic duplicated or budget applied around the wrong span. Zero: fail-open checkout possible. |
| 4 | Privacy and decision log | 10 | Full: digests only in requests and logs, reason codes never in model-visible text, one record per assessment, log sink failure isolated. Partial: one leak path (e.g. exception message logged). Zero: raw session or user id anywhere. |
| 5 | Code quality and MRO hygiene | 5 | Cooperative `__init__` with `*args, **kwargs`, `super()` everywhere (no hard-coded base class), typed, readable, no dead code. |
| 6 | ANSWER.md trade-offs | 10 | Full: names at least two real production concerns with a position, e.g. the cart lock held across a 150 ms network call (throughput vs consistency), review-at-cart deferred to checkout, breaker in front of the client, idempotent decision ids, the risk of fail-open abuse during a brownout. Partial: generic. Zero: empty. |
Total: 100
