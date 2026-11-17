# genai/ai-t1 - Prompt cache hit rate fell to zero after the release; latency and cost up

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** AI Integration page (3: context
engineering and caching, 7: observability)

## Symptom

Since the 2026-11-10 release, Kestrel's assistant is slower to the first token. The provider invoice
is three times higher, but the internal cost dashboard is flat. The provider console shows the prompt
cache hit rate fell from 87% to about 2%. Read `evidence/PAGE.md` first.

## What you have

| Path | What it is |
|---|---|
| `evidence/PAGE.md` | the page and the thread |
| `evidence/release-notes.md` | what changed on 11/10 |
| `evidence/usage-by-worker.log` | provider usage per request, with pod and worker pid |
| `evidence/request-dump-pid41.json`, `evidence/request-dump-pid38.json` | two requests from different workers |
| `evidence/dashboards.txt` | our cost dashboard vs the invoice, latency |
| `assistant/request_builder.py` | builds every request; `prefix_bytes()` / `prefix_hash()` show the cached prefix |
| `assistant/cost.py` | the dashboard's cost formula |
| `assistant/tools.py` | tool definitions and prompt text (complete) |
| `scripts/demo.py` | `make demo` runs 10 worker processes, each with its own hash seed, against a simulated provider cache |

Prices (USD per million tokens): input 3.00, cache write 3.75, cache read 0.30, output 15.00.

## Your task

1. Find the root cause with evidence. Explain why only a few requests still hit, why the hit rate
   tracks worker processes, and whether the new timestamp is to blame. Explain why the dashboard
   stayed flat.
2. Fix `assistant/request_builder.py` so the cached prefix (tools, then system up to the breakpoint) is
   byte-identical across processes, restarts and requests. Keep the tools sorted by name and keep
   exactly one breakpoint, on the last static system block. Dynamic data (time, store, question,
   history) stays after the breakpoint.
3. Fix `assistant/cost.py` so cache writes and reads are priced, and the dashboard matches the invoice.
4. Verify with `make demo` and `make test`. Write `ANSWER.md`.

## Acceptance criteria (what the grader checks)

- Identical prefix hash across worker processes with different `PYTHONHASHSEED` values.
- Sorted tools, one breakpoint after the static system prompt, no dynamic data in the prefix.
- Correct cost for cache writes and reads.
- `ANSWER.md` names the mechanism with evidence and rules out the timestamp.

## How to run

```bash
make setup
make demo
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade genai/ai-t1
make clean
```
