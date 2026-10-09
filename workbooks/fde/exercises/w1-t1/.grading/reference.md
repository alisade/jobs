# Reference: fde/w1-t1

**Injected fault:** `storefront_prompt/tools.py` `enabled_tool_names` returns
`list(set(...))`. Set iteration order for `str` depends on the per-process hash salt, so
each of the 16 worker processes (4 pods x 4 uvicorn workers) builds a different tools array
and a different "# Tools in this deployment" line in the static system text. The prompt
cache keys on the exact prefix bytes (tools, then system, then messages), so a session whose
next turn lands on another process re-writes its whole conversation. Hit rate 88.7% -> 62.3%
overall, 92.8% -> 38.4% on the first call of turn 2+.

**Red herrings:** the anthropic SDK bump (#423) and the hourly `local_time` in the session
context (#421, after the breakpoint). Cart/page changes re-reading the conversation exist on
both days and are expected blueprint behavior.

**Fix:** `.grading/solution/storefront_prompt/tools.py`:

```python
wanted = set(CORE_TOOLS) | {t for t, f in OPTIONAL_TOOLS.items() if flags.get(f)}
for extra in flags.get("extra_tools", []): validate; wanted.add(extra)
return [name for name in TOOL_ORDER if name in wanted]
```

`dict.fromkeys(...)` over an ordered sequence is the other idiomatic answer. Sorting
alphabetically is deterministic but changes the order the evals were tuned on.

**Why the pre-deploy check missed it:** one local process has one hash salt, so turn 2 read
from cache. The failure needs two processes.

**Model answer:** `.grading/solution/ANSWER.md`.

**Interview follow-ups:** Where else does per-process nondeterminism leak into prompts?
(`set`, `os.listdir`, `glob`, `dict` built from a set, `id()`-based ordering, `json.dumps`
of objects with set fields, timestamps or UUIDs in "static" text, skill registries loaded
from the filesystem.) Why not just pin PYTHONHASHSEED? (Hides the bug, re-breaks on any
other process type, weakens hash-flooding protection.)
