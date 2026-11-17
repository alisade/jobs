# platform/ai-t1 - The agent's PR said no-op, the plan had a replace

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** AI Integration (context engineering, verification); Week 6 (plan as the verification step)

## Scenario

Tessellate's (fictional) import agent drafts import blocks, runs `terraform plan` through a tool, asks
the model for a plan summary, verifies, and opens a pull request only for import-only plans. PR #212
said "plan: 8 to import, 0 to change, 0 to destroy, verification passed". The reviewer ran the plan:
14 imports and a forced replacement of `google_sql_database_instance.riq_main`, the RIQ production
database. The agent is paused. The fix has to make this impossible, not less likely.

## What you have

| Path | What it is |
|---|---|
| `evidence/` | page, transcript, PR body, review comment, and the plan JSON of the run (`plan-run-212.json`) |
| `agent/pipeline.py` | one run: tool, model summary, verify, open PR (`make repro`) |
| `agent/tools.py` | the `terraform_plan` tool |
| `agent/verify.py` | the gate |
| `agent/llm.py` | a deterministic stand-in for the model: it reports what it can see in the tool output |
| `agent/prompt.py` | the system prompt |

## Your task

1. `make repro` and the evidence: why did verification pass, and why did the model say 8 imports?
2. Decide whether the prompt line matters.
3. Fix `agent/verify.py`: compute counts from the full plan JSON (`summarize(plan)` returning import,
   add, change, destroy, replace; a replace in either order counts as one add and one destroy), ignore
   the model's claim for the verdict, and fail closed on anything it cannot read (bad JSON, missing
   `resource_changes`, `errored`, unknown actions). Pass only for at least one import and zero add,
   change and destroy.
4. Fix `agent/tools.py` so the model gets a complete, compact summary (valid JSON, under the 8000
   character limit, naming replaced and destroyed addresses) instead of truncated raw JSON.
5. Make the PR body use the verified counts. Write `ANSWER.md`.

## Acceptance criteria (what the grader checks)

- The incident plan: 14 imports, 1 add, 1 destroy, 1 replace, no PR.
- Any of delete-create, create-delete, delete, update, create blocks; a clean import-only plan opens a
  PR whose body carries the verified counts.
- A model claiming a clean plan cannot change the verdict.
- Bad JSON, a plan without resource_changes, a truncated file and an errored plan all fail closed.
- Tool output is valid JSON, at most 8000 characters, and names `google_sql_database_instance.riq_main`.

## How to run

```bash
make setup
make repro
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade platform/ai-t1
make clean
```

## What to submit

`agent/verify.py`, `agent/tools.py`, `agent/pipeline.py` (if changed), `ANSWER.md`.
