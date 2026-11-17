# Reference: audit/ai-t1

Fixed file: `.grading/solution/promptkit/prompt.py`.

**What the logs show.** `usage-after.jsonl`: `cached_tokens` is 0 on 25 of 25 calls, while
`prompt_tokens` is ~5,360 as before (no tokenizer change) and latency rises with the uncached tokens.
Before: ~91% of input tokens cached, one cold call per instance.

**Cause (two parts).**
1. PR #2411 put `ControlPilot run <id> | started <ts> | sample <CHG-...>` at the top of the system
   instruction. The simulator, like the real implicit cache, serializes tools, then system, then
   contents; two requests now diverge at the sample id, a few dozen characters into the system text,
   which is below the 1,024-token minimum, so nothing is cached. One request header made a 5k-token
   static procedure uncacheable.
2. The tool list is built by iterating `ENABLED_TOOLS`, a `set` of strings. String hashing is
   randomized per process (`PYTHONHASHSEED`), so each Function instance declares the tools in a
   different order, and the tools come first in the prefix. Within one process the order is stable,
   which is why removing only the header fixes a single-process test but not production with two
   instances (PR #2417).

**Red herring.** The model bump moves the cache to a new key once: the first call per instance on
-002 is cold and every later call hits, if the prefix is stable. 25 misses of 25 is not a model effect.

**Fix.** Ordered, sorted tool declarations; a static system instruction; the sample (and, if needed,
the run id) only in the last user content; run metadata in logs and request labels. Prevention: a
unit test that builds the prefix in subprocesses with several hash seeds and asserts it is
byte-identical, plus an alarm on `cached_content_token_count / prompt_token_count` per batch. When the
prefix must be guaranteed (large evidence corpora), use explicit context caching (a cached content
resource with a TTL) instead of relying on implicit caching.
