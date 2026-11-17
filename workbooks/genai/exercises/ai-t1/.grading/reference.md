# Reference: genai/ai-t1

## Root cause
`build_request` does `[TOOL_DEFS[name] for name in ENABLED_TOOLS]`, and `ENABLED_TOOLS` is a `set`.
Python randomizes string hashing per process (PYTHONHASHSEED), so set iteration order differs
between interpreter processes. Each gunicorn worker (4 per pod x 9-14 pods) builds the tools in its
own order. The provider caches the prefix tools, then system, up to the breakpoint, so every worker has
a different prefix, and a request hits only if the same worker wrote that prefix within the 5-minute
TTL. With about 48 workers, that is roughly 2%. Before the release the tools were a literal list, so
every worker produced the same bytes.

Evidence: the two dumps differ only in the order of `tools`. In usage-by-worker the hits are pid 41 on
the pod that already wrote at 09:00:03, and so on. `make demo` gives 10 prefixes and 0% before the fix,
and one prefix and 90% after.

Red herring: the timestamp and store id are in the user message, after the breakpoint on the last
system block, so they do not touch the cached prefix. Dropping the timestamp would change nothing.

Dashboard: `cost_usd` ignored `cache_creation_input_tokens` (9,840 per request at $3.75/MTok) and
`cache_read_input_tokens`. Before the release most of the prefix was cheap reads that it also ignored,
so the error was small. After, every request wrote 9,840 tokens at 1.25x, and the dashboard missed
all of it.

## Fix
`sorted(ENABLED_TOOLS)` (or an ordered tuple). A correct `cost_usd` with all four token classes.

## Prevention
- A CI test that builds the request under several PYTHONHASHSEED values and asserts one prefix hash.
- Log `prefix_hash` and cache read/write tokens per request. Alert when the hit ratio drops below 70%.
- Reconcile the dashboard with the invoice daily.
- Review rule: nothing built from an unordered collection goes into the prompt prefix.
