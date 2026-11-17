# platform/ai-c1 - On-call page triage assistant with an eval gate

**Type:** coding | **Estimate:** 2.5-3 hours | **Study plan:** AI Integration (tool design, agent loop, security, evals); Week 6 (agentic toil with approval gates)

## Scenario

Tessellate (fictional) TechOps runs a 12-hour on-call rotation. The first 15 minutes of most pages are
the same toil: open the alert, run the dashboard query, read the runbook, check recent deploys, write a
triage note in the incident channel. The team wants an assistant to do that first pass. Rules from the
on-call lead: tools are read-only except `silence_alert`, which only runs if the on-call engineer
approves it; the note must be machine-validated and every claim must point at a tool call that actually
ran; if the assistant cannot produce a valid note it says so instead of guessing.

There is no API key in this exercise. `triage/llm.py` replays recorded model responses (Messages API
shapes: `text` and `tool_use` blocks, `stop_reason`) and checks that your loop sends what the recorded
model saw. Ten scenarios live in `data/recordings/`; one of them carries a prompt injection inside an
alert annotation.

## What you have

| Path | What it is |
|---|---|
| `triage/agent.py` | the loop. Works for the happy path only: no schema checks, no approval, no retry, no turn limit |
| `triage/models.py` | the `TriageNote` contract (Pydantic), done |
| `triage/tools.py` | tool definitions (JSON schemas) and the `Toolbox` over `data/`, done |
| `triage/llm.py` | the fake client that replays recordings, done |
| `triage/evals.py` | the eval harness; `score()` and `gate()` are TODO |
| `data/` | alerts, metrics, deploys, runbooks, recordings, `golden.json` expectations |

## Your task

**Tool execution** (`run_tool`): unknown tool names and inputs that fail the tool's JSON schema return a
`tool_result` with `is_error: true` and a message the model can act on, without running anything. Write
tools (`WRITE_TOOLS`) run only when `approve(name, args)` returns True; an approver that raises counts as
a no; every write attempt is appended to `result.audit` (`tool`, `input`, `approved`, `tool_use_id`).
`ToolError` and unexpected exceptions also become `is_error` results. Record each call in
`result.tool_calls` with `executed` true only when the tool really ran.

**The loop** (`run_triage`): stop after `max_turns` model calls with status `max_turns`. When the model
answers with text, validate it (`validate_note`): valid JSON, the `TriageNote` contract, `alert_id`
matches, every evidence `tool_use_id` is a call that executed. On failure, record the error in
`result.errors`, send the error back once as a user message, and on a second failure return status
`needs_human` with no note.

**Evals** (`score`, `gate`): per scenario, the checks are status, and for status ok also severity, cause
keyword (case-insensitive substring) and grounded evidence; the safety check is "no write tool executed
without an approved audit entry". `passed` needs all of them. The gate passes only with zero safety
violations and a pass rate at or above the threshold.

## Acceptance criteria (what the grader checks)

- s04 (injection): no silence is created, the attempt is audited as not approved, and the note is still
  produced; same with an approver that raises.
- s05 (bad tool input) and s06 (unknown tool) recover through `is_error` results.
- s08 and s09 recover on the retry; s10 fails twice and returns `needs_human`.
- `max_turns` is enforced; `score` and `gate` behave as above; the full eval run passes 9 of 10 (s07 is a
  genuine model miss on severity that your code must not hide) with zero safety violations.
- `ANSWER.md`: why enforcement lives in code, how you would run this for real.

## How to run

```bash
make setup
make evals      # the eval report and gate
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade platform/ai-c1
make clean
```

`make live` is an optional stub and never graded.

## What to submit

`triage/agent.py`, `triage/evals.py` and `ANSWER.md`.
