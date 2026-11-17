# audit/w3-c1 - ADK CM-03 tester with scoped tools, guardrail callbacks and an execution log

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 3 (Mon: ADK agents and tools; Wed: callbacks as guardrails)

## Scenario

ControlPilot is moving its CM-03 tester onto Google's Agent Development Kit (ADK) so it can later be
deployed on Gemini Enterprise Agent Platform. All of ControlPilot's skills share one tool registry
(`tester/systems.py`), and that registry includes `close_change`, a write tool that belongs to the
change-management team's remediation skill. The change system also holds tickets outside the
sample, including a board-confidential one.

The audit manager's conditions for production: the tester can read only the sampled changes, can
never call a write tool other than `record_result`, has a hard budget of tool calls, leaves an
execution log that an external auditor can follow call by call, and its final answer is checked in
code against what it actually recorded. "The prompt tells it not to" is not a control.

The model is `tester/scripted.py`: an ADK `BaseLlm` subclass that plays a script, so a test can make
"the model" do anything, including the wrong thing. ADK itself runs for real. No network.

## What you have

| Path | What it is |
|---|---|
| `tester/systems.py` | mock systems, the shared tool registry, `EXECUTED` (every tool body that actually ran) - do not edit |
| `tester/scripted.py` | the scripted model - do not edit |
| `tester/guard.py` | the callbacks you write |
| `tester/agent.py` | the agent wiring, the run and the summary check you write |
| `tests/scripts.py` | a happy-path script |

## Your task

1. `make_before_tool(sample_ids, max_tool_calls)`: an ADK `before_tool_callback`. Count every
   tool call in session state (`tool_calls`). Block (return `{"error": <reason the model can act
   on>, "blocked_by_guard": True}`, which ADK sends back as the tool result without running the
   tool) when: the budget is exceeded (block every call after the limit); the tool is not in
   `ALLOWED_TOOLS`; a `change_id` argument is not in the sample; a `pr_number` is not linked to a
   sampled change (use `systems.TICKETS`); `record_result` has a result other than pass,
   exception or needs_review. Otherwise return None.
2. `make_after_tool(log)`: an ADK `after_tool_callback` that appends exactly one entry per tool
   call: `seq` (1-based), `tool`, `args`, `blocked` (bool), `reason` when blocked, `result_sha256`
   (`digest()` of the tool result: SHA-256 of canonical JSON) and `at` (UTC ISO time).
3. `build_agent()` registers only the allowed tools (never offer `close_change` to the model) and
   both callbacks. `run_test(llm, sample_ids)` runs the agent once with `Runner` and an
   `InMemorySessionService` session whose state holds `sample_ids`, captures the final text, and
   reads the recorded results back from the session state.
4. Make `ResultRow` / `TestSummary` strict (no extra keys, `control` is `"CM-03"`, results limited to
   the three values). `check_summary()` validates the final text and cross-checks it: it covers
   exactly the sample, no duplicates, and each row matches what `record_result` stored. Any
   problem means `status="needs_review"` with the problems listed.
5. `ANSWER.md`: why each guardrail is a callback and not an instruction, and what the execution log
   lets an auditor reconstruct.

## Acceptance criteria (what the grader checks)

- Out-of-sample tickets, unlinked PRs and out-of-sample `record_result` calls are blocked and never executed.
- `close_change` is not offered to the model and never runs.
- The budget blocks every call after the limit; the run then ends in needs_review.
- One log entry per call, in order, with blocked flags, reasons and result digests.
- The final summary is validated and cross-checked against session state.

## How to run

```bash
make setup
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade audit/w3-c1
make clean
```
