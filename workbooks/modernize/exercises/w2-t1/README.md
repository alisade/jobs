# modernize/w2-t1 - The reverse-engineer skill missed the batch job's tables

**Type:** troubleshooting | **Estimate:** 1.5 hours | **Study plan:** Week 2 (Tue: subagents and context; Fri: tool design for agents)

## Symptom

Two weeks ago the pod ran the team's `reverse-engineer` skill on the ClaimDesk checkout and
planned the EAP 8 schema migration from the spec it wrote. Last night's month-end rehearsal
failed: `reporting-batch` hit `ORA-00942` on `LOSS_TRIANGLE`. The spec says reporting-batch has
no database access. A developer's draft postmortem blames the model ("it hallucinated, the
context window filled up") and proposes a bigger model. You own the skill. Read
`incident/PAGE.txt` first.

## What you have

| Path | What it is |
|---|---|
| `incident/` (created by `make setup`) | the page, the agent run transcript (JSONL), the spec excerpt it produced, the draft postmortem |
| `repo/` (created by `make setup`) | the ClaimDesk checkout the agent scanned |
| `skill/reverse-engineer/SKILL.md` | the skill |
| `skill/reverse-engineer/scripts/scan_db.py` | the tool the skill tells the agent to run (current version, yours to fix) |
| `scripts/scan_db_v1.py` | frozen copy of the version used in the 2026-10-28 run (do not edit) |

## Your task

1. Find the root cause and prove it from the transcript, the repo and the tool. Is the
   postmortem right? What did the model actually see?
2. Fix the tool so this class of failure cannot happen silently, and fix the skill so the agent
   checks coverage before it claims absence. Keep the default output small enough for a context
   window.
3. Write `ANSWER.md`: Approach, Root cause (commands and output excerpts), Fix (and how you
   verified it), Trade-offs / production follow-ups, including the failure-mode log entry you
   would add for the skill.

## Contract for the fixed scanner (the grader relies on it)

- `scan(root) -> list[Hit]` unchanged.
- `summarize(hits) -> dict[table, {"count": int, "modules": sorted list of str}]`: complete, never paged.
- `render(hits, limit=200, offset=0) -> str`: first line `# db touchpoints: total=<N> shown=<a>-<b>`;
  when hits remain after the page, the last line starts `# TRUNCATED` and says how many and which
  `--offset` to use next.
- `main(argv)` prints the summary first, then one page; accepts `--limit` and `--offset`.

## Acceptance criteria (what the grader checks)

- The summary lists all 14 tables with the right modules; pages say when they are cut; offsets work.
- The default tool output names every table and module and stays under 70,000 characters.
- `SKILL.md` tells the agent to read the summary, page on truncation, and not claim absence without proof.
- `ANSWER.md` names the mechanism with evidence; "the model hallucinated" does not pass.

## How to run

```bash
make setup      # venv + incident bundle
make scan       # the tool as the agent ran it
make test       # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade modernize/w2-t1
make clean
```

Useful: `jq -r 'select(.type=="tool_result") | .lines' incident/transcript.jsonl`,
`python3 skill/reverse-engineer/scripts/scan_db.py repo --limit 100000 | wc -l`.
