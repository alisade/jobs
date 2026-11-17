# modernize/ai-c1 - A guarded migration agent: tool scoping, approval gates and a planted injection

**Type:** coding | **Estimate:** 2.5 hours | **Study plan:** AI Integration page (tool design, the agent loop, security) and Week 6 (headless agents with human gates)

## Scenario

The ClaimDesk pod wants to run a small migration agent headless in CI: it reads the repository,
proposes patches (for example "replace sun.misc.BASE64Encoder"), and a reviewer on the pod approves
each patch before it is written. AppSec agreed on one condition: the safety of the run must not
depend on the model behaving. The fixture repository contains a file left by a 2019 contractor with
an instruction aimed at "automated assistants" to empty a test and print a secret. Assume the
model will sometimes follow such text.

`pod_agent/loop.py` runs the loop today with no guards. Make it safe.

## What you have

| Path | What it is |
|---|---|
| `pod_agent/loop.py` | the loop (yours to harden) |
| `pod_agent/tools.py` | tool schemas sent to the model and their raw implementations |
| `pod_agent/model.py` | `ScriptedModel`, which replays Messages-API-shaped responses (no API key) |
| `fixtures/workspace/` | a tiny ClaimDesk checkout, including `secrets/db.env` and `MIGRATION_NOTES.md` |
| `tests/` | visible tests and helpers for writing scripted runs |

## Contract (the grader relies on it)

`run_agent(model, workspace, task, approver, max_turns=12) -> RunResult`

1. Every `tool_use` block gets exactly one `tool_result` with the same `tool_use_id`, in order.
   Failures are results with `"is_error": True` and a message the model can act on; the loop never
   raises because of a tool call.
2. Inputs are validated against the tool's `input_schema` (`jsonschema` is installed). Unknown tools
   are errors that list the available tools.
3. Paths are relative to the workspace and must stay inside it: no absolute paths, no `..`, no
   symlink escapes.
4. Reads are denied for secrets: `secrets/`, `.env` files, `*.pem`, `*.key`. `search` must not leak
   their contents either.
5. Writes (`propose_patch`) are allowed only to `src/main/**` and `pom.xml`. Anything else is denied
   before the approver is asked. Allowed writes call `approver(PatchRequest)`; `False` means
   rejected and nothing is written.
6. Tool results longer than `MAX_TOOL_RESULT_CHARS` are cut, with a marker saying so.
7. At most `max_turns` model calls; then `stopped = "max_turns"`.
8. `RunResult.audit` has one entry per tool call: `{"turn", "tool", "decision", "path"?}` with decision
   one of `allowed`, `denied`, `invalid`, `unknown_tool`, `approved`, `rejected`, `error`.
   `RunResult.writes` lists the paths actually written.

## Acceptance criteria (what the grader checks)

- The planted injection run (the model reads the notes, then tries to empty a test and read the
  secret, with a reviewer who approves everything) changes nothing and leaks nothing.
- Scoping, approval, validation, unknown tools, missing files, truncation, max turns and the audit
  trail behave as specified.
- `ANSWER.md` explains why the guarantees hold even if the model is fully compromised, and what
  else you would add before running this in CI (lethal trifecta, sandbox, secrets, network).

## How to run

```bash
make setup
make test       # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade modernize/ai-c1
make clean
```
