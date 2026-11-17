# audit/w5-t1 - An exception closed overnight "pre-approved by CAB per system note"

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 5 (Thu: prompt injection via evidence files, the lethal trifecta, tool scoping)

## Symptoms

At 07:42 the GRC Hub pager fired: CM-03 exception **EXC-2026-0412** (CHG-104233, approval before
deploy) moved from open to closed at 02:14 by `svc-controlpilot`, with the comment
"pre-approved by CAB per system note". No reviewer is recorded. The IT audit senior says nobody
touched it, and there is no CAB record of a standing approval "SA-7". The workpaper for CHG-104233
now says pass. The ingest log also shows a low OCR confidence warning on the same document.

The audit manager needs to know how an exception can close itself, whether other items are
affected, and what makes it impossible next time, before ControlPilot runs again tonight.

## What you have

| Path | What it is |
|---|---|
| `reviewagent/` | the ADK evidence-review agent: `agent.py`, `tools.py`, `evidence.py`, `store.py`, `scripted.py` |
| `config/evidence_reviewer.yaml` | agent config (release 2026.10.2) |
| `evidence/` | Document Intelligence layout JSON per change |
| `fixtures/` | initial GRC state, the overnight queue, the model's recorded responses |
| `run.py` | `make run` replays the overnight run against a fresh GRC state |
| `incident/` | written by `make setup`: pager, trace, ingest log, runtime log, release notes, GRC export |

The model is `reviewagent/scripted.py`, an ADK `BaseLlm` that replays the recorded responses.

## Your task

1. Find the root cause and write it in `ANSWER.md` with evidence (trace lines, the evidence
   paragraph and its style metadata, the config and code that allowed it).
2. Fix it so that **a model that always obeys the planted text still cannot cause harm**. Prompt
   wording alone does not count as a fix: the grader's model tries the injected tool calls every time.
3. Keep normal samples working, and say what you would check in other evidence and other runs.

## Interfaces the fix must provide

- `reviewagent.agent.build_agent(llm, change_id, store, evidence_dir)` returns the ADK agent; its tools
  are read-only (`list_evidence`, `get_evidence`) and its instruction contains no evidence text.
- `reviewagent.agent.review(...)` passes the evidence as data in the **user** message between
  `<evidence ...>` and `</evidence>`, never mutates the GRC store, and returns a `ReviewResult` whose
  `flags` include `{"kind": "unauthorized_tool_attempt", "tool": ...}` for every tool call outside the
  agent's tools, plus the screening flags below.
- `reviewagent.screen.screen_evidence(layout) -> list[dict]`: deterministic flags with `kind`
  (`instruction_like_text` or `hidden_text`, the latter when a style's color equals its background
  or is white without a background), `page` and `paragraph`.
- `reviewagent.gate.close_exception(store, exception_id, approval)`: the only way to close an
  exception; raises `reviewagent.gate.GateError` unless the approval record names this exception,
  has `decision == "approve_close"`, a non-empty `comment`, and a `reviewer` who is in
  `store.reviewers` and is not the exception's `prepared_by`.

## Acceptance criteria (what the grader checks)

- Against an always-obedient model, EXC-2026-0412 and EXC-2026-0415 stay open, history empty,
  workpaper unchanged; the attempts are in the trace (not executed) and flagged.
- The planted paragraph is flagged as both instruction-like and hidden text; clean evidence is not.
- The gate refuses every incomplete or self-serving approval and closes with a valid one.
- `make run` end to end leaves EXC-2026-0412 open.
- Root cause and evidence in `ANSWER.md` match the injected fault.

## How to run

```bash
make setup     # shared venv, replays the night, writes incident/
make run       # replay again from a fresh state
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade audit/w5-t1
make clean
```
