# bw-shop-agent release 2026.10.06

Deployed 2026-10-06 09:20 UTC to prod (4 pods x 4 uvicorn workers). Diff: `release-2026.10.06.diff`.

| PR | Change | Risk (reviewer) |
|---|---|---|
| #418 | Dedupe enabled tools before building the tools array; merchants can list `extra_tools` in flags.json. Fixes INC-2291 (a merchant enabling `present_comparison` both by flag and by extra got `400 tools: Tool names must be unique`). | low, pure refactor |
| #421 | Session context shows `local_time` (rendered to the hour) instead of `local_date`, so "is the store open now" answers are right. The context block is after the cache breakpoint. | low |
| #423 | `anthropic` 0.121.0 -> 0.122.0 (typing fixes, new beta headers). | low |

Pre-deploy checks: unit tests green, `smoke_chat.py --vertical retail` green on one local
process, cache check on one local process: `cache_read_input_tokens` non-zero from turn 2.
