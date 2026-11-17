# assistant 2026.11.10 (deployed 2026-11-10 21:30 PT)

- New "compare products" capability: the system prompt now asks for a side-by-side comparison when the
  customer names two or more products. `max_tokens` raised from 512 to 2048 so comparisons are not cut off.
- Gateway: no code change in this release. Gateway config unchanged since 2026-08 (`timeout_s=10.0`,
  `retries=3`, fallback model enabled). The fallback model was added for the July provider outage.
- Answers are returned in one piece (non-streaming) for the comparison card layout.
