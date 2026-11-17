# aiarch/ai-t1 - Bedrock spend tripled after release 3.1.0

**Type:** troubleshooting | **Estimate:** 1-1.5 hours | **Study plan:** AI Integration (3 Context engineering and caching) and Week 6 (cost tuning)

## Symptom

FinOps reports that daily Bedrock cost for the Lighthouse help desk agent went from about
USD 41 to about USD 128 with flat traffic, starting the day release 3.1.0 shipped. On-call
thinks the system prompt fell under the model's minimum cacheable size, or that the 5-minute
cache TTL is too short. Read `incident/PAGE.txt` first (created by `make setup`).

## What you have

| Path | What it is |
|---|---|
| `incident/PAGE.txt` | the ticket and on-call notes |
| `incident/converse-usage.jsonl` | Converse usage blocks before and after the release |
| `incident/release-3.1.0-notes.md`, `incident/daily-cost.txt` | what changed, and cost per day |
| `lighthouse/builder.py` | builds the Converse request for each turn (edit this) |
| `lighthouse/bedrock_stub.py` | a stub of Converse prompt caching: prefix up to the last cachePoint, minimum size, TTL (works as shipped) |
| `lighthouse/tools.py`, `prompts/system.md` | tool specs and the system prompt |

## Your task

1. Find the root cause from the usage logs and the builder; explain why the minimum-size and
   TTL theories do not fit the evidence.
2. Fix `lighthouse/builder.py`: everything before the cache point is byte-identical across
   requests and users; the time, request id and user still reach the model, after the cache
   point; the question stays the last user content; history is kept. Harden the prefix against
   tool registration order too (plugins register tools in load order).
3. Verify with `make test`.
4. Write `ANSWER.md`: Approach, Root cause (with evidence), Fix and verification, Trade-offs.

## Acceptance criteria (what the grader checks)

- Cache reads from turn 2 and across users; identical prefix bytes; dynamic data after the
  cache point; question and history placement; cost for 100 conversations under budget.
- `ANSWER.md` names the per-request text before the cache point with evidence.

## How to run

```bash
make setup     # evidence bundle + aiarch/.venv
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade aiarch/ai-t1
make clean
```

## What to submit

`lighthouse/builder.py` and `ANSWER.md`.
