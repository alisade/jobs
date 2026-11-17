# ANSWER: fde/w1-t1 cache_read collapsed after a harmless release

## Approach

Started from the dashboard rather than the diff. `run/dashboard.txt`: overall hit rate
88.7% on 2026-10-05 vs 62.3% on 2026-10-06, and the first call of turn 2+ (where the
previous turns' conversation should be read back) 92.8% vs 38.4%. Same traffic shape, so
the cached prefix itself changed shape. Within a turn (same worker) rounds still read
their predecessors; the misses cluster on turn openings, i.e. when the load balancer
moves a session to another process. That points at something that differs per process.

Ruled out:
- The SDK bump (#423): the SDK serializes the body we give it; the replay builds request
  bodies without the SDK and shows the same drop.
- The hourly `local_time` (#421): it is in the second system block, after the static
  block's breakpoint. It costs one conversation re-read per session per hour on both days
  (13:00/14:00 buckets look alike), and `build_dynamic_context` at 13:01 and 13:59 is
  byte-identical.
- Cart/page changes re-reading the conversation (`cache_read=1982` mid-turn on one worker
  after a cart write): present on both days, it is the blueprint's documented behavior.

## Root cause

PR #418 changed `enabled_tool_names` to collect names into a `set` and return
`list(names)`. Iteration order of a set of `str` follows the strings' hashes, and CPython
salts `str` hashes per process (PYTHONHASHSEED is random unless pinned). Every uvicorn
worker therefore built its own tool order, and the same set also feeds the
"# Tools in this deployment" line of the static system text. The cache key is the exact
prefix bytes in order tools -> system -> messages, so the 16 processes sent 16 different
prefixes:

```
$ for s in 1 2; do PYTHONHASHSEED=${s} PYTHONPATH=. python -c "import json; from storefront_prompt.tools import enabled_tool_names; print(enabled_tool_names(json.load(open('config/flags.json')))[:5])"; done
['get_fulfillment_options', 'present_products', 'present_suggestions', 'add_to_cart', 'remove_from_cart']
['get_orders', 'search_products', 'remove_from_cart', 'get_product_details', 'get_preferences']
```

Each process's static prefix stays warm on its own traffic, so the static part still
reads; what is lost is the conversation. Session 0d793cfb: turn 1 on worker 7
(`turn=1 round=3 ... cache_read=2497`), turn 3 lands on worker 1, whose tools prefix is
different, so the whole conversation is written again:
`worker-1.log ... session=0d793cfb turn=3 round=1 ... cache_read=1982 cache_write=1323`
(1982 tokens is exactly worker 1's tools + static system). With 16 processes, 15 in 16
turn openings move to a different prefix.

Why the pre-deploy check passed: it ran one local process. Within one process the order
is stable, so turn 2 read from cache. The bug only exists across processes.

## Fix

`storefront_prompt/tools.py`: keep the set for membership and dedupe, take the order from
`TOOL_ORDER`: `return [name for name in TOOL_ORDER if name in wanted]`. Unknown extras
still raise; an extra takes its release slot; a duplicate appears once. The static
system line uses the same function, so it is fixed too.

Verified: `make test` green; the two-seed probe above prints the same list;
`make replay` -> 88.4% overall, 92.3% on turn openings (yesterday 88.7% / 92.8%); one
distinct prefix digest across all 16 workers.

## Trade-offs / what I would do in production

- CI test that builds the prefix under several PYTHONHASHSEED values in subprocesses and
  asserts one digest; and a "prefix golden file" check so any prefix change is a reviewed
  diff, not a side effect.
- Ban `set`/`frozenset` iteration (and unsorted `dict` from untrusted order, `os.listdir`,
  `glob`) on the path that builds tools and the static prompt; a ruff rule or review
  checklist.
- Alert on cache hit rate per release and log a prefix digest per worker at start-up so
  drift is visible in one query.
- Pre-deploy cache check must run against more than one process (or a pinned-seed matrix).
- Pinning PYTHONHASHSEED fleet-wide would also "fix" it but hides the bug and weakens hash
  DoS protection; deterministic order in code is the right fix.
