# Rubric: genai/ai-t1 Prompt cache hit rate fell to zero after the release
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh (several guards pass on the starter) |
| 2 | Root cause identified | 25 | Full: the tool list is built by iterating a Python `set` (`ENABLED_TOOLS`). String hashing is randomized per interpreter process (PYTHONHASHSEED), so each of the 48 gunicorn workers serializes the tools in a different order. Tools come first in the cached prefix, so the prefix bytes differ per worker, and only requests that land on a worker that already wrote the cache within the TTL hit. Partial (10-15): "tool order changed" without the per-process hash randomization, or "the prefix changed" without saying what. Zero: blames the timestamp or the provider. |
| 3 | Evidence | 20 | Full: the two dumps differ only in tool order; usage-by-worker shows hits only on a pid that already wrote (pid 41 at 09:00:11, pid 38 at 09:00:22); `make demo` gives 10 prefixes and 0% before the fix, 1 prefix after; the release note "tools now from a feature-flag set". Partial: one or two. |
| 4 | Red herring ruled out | 5 | The timestamp is in the user turn, after the breakpoint, so it does not affect the cached prefix (proved by `prefix_bytes` or the demo after the fix). The store id is after it too. |
| 5 | Fix quality | 10 | `sorted()` (or an explicit ordered list) for the tools; one breakpoint; no dynamic data before it; cost formula with all four token classes. The dashboard explanation: it ignored cache write tokens, which are now 9,840 per request at 1.25x. |
| 6 | Prevention | 10 | Concrete: a CI test that builds the request under several PYTHONHASHSEED values and compares prefix hashes; log the prefix hash per request; alert on cache hit ratio; reconcile the dashboard with the invoice daily; never iterate sets or dicts of unknown order into prompts. Partial: generic. |
Total: 100
