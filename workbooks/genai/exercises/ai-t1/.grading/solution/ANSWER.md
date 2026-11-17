# ANSWER: genai/ai-t1 Prompt cache hit rate fell to zero after the release

## Approach

I diffed the two request dumps first: the only difference before `messages` is the order of `tools`.
Then I read usage-by-worker for which requests still hit, and ran `make demo` with 10 hash seeds.

## Root cause

`ENABLED_TOOLS` is a Python set, and `build_request` iterates it to build the tools list. String hashes
are randomized per process (PYTHONHASHSEED), so each of the ~48 gunicorn workers emits the tools in a
different order. Tools are the start of the cached prefix, so every worker has a different prefix.
Only a request that lands on a worker that already wrote the cache within 5 minutes hits.
- pid 41 dump: `check_inventory, store_hours, get_order_status, search_products, start_return`. pid 38:
  `store_hours, get_order_status, search_products, start_return, check_inventory`. System and
  breakpoint are identical.
- Usage: hits only on repeat pids (2kq9p pid 41 at 09:00:11 after its 09:00:03 write; 7xwr2 pid 38 at
  09:00:22).
- `make demo` before the fix: 10 distinct prefixes, 0% hits. After: 1 prefix, 90%.

The timestamp is not the cause. It sits in the user turn after the breakpoint, and the demo after the
fix shows one prefix while timestamps still vary.

The dashboard stayed flat because `cost_usd` ignored cache tokens. It now misses 9,840 write tokens per
request at $3.75/MTok, which is the 3x on the invoice.

## Fix

`sorted(ENABLED_TOOLS)` gives a byte-stable prefix. `cost_usd` now prices input, cache write, cache
read and output. Tests pass and the demo shows 90% hits.

## Trade-offs / what I would do in production

- Add a CI test across PYTHONHASHSEED values.
- Log the prefix hash per request and alert on the hit ratio.
- Reconcile the dashboard with the invoice daily.
- Keep all per-request context after the breakpoint.
