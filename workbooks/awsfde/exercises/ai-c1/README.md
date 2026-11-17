# awsfde/ai-c1 - Agent eval harness as a CI gate

**Type:** coding | **Estimate:** 2 hours | **Study plan:** AI Integration (5: evals; 4: security); Week 3 Fri (retrieval evals)

## Scenario

Release 2026.11.10 of Tidewater Ask changes the system prompt and upgrades the model. The release
manager asks the FDE team one question: "is it safe to ship?" Today the answer is a few people
chatting with the agent in staging. You replace that with a harness that runs in CI: 15 golden cases
(normal questions, edge cases and two prompt-injection attempts), each recorded three times against
the baseline release and the candidate, scored by deterministic checks first, with an optional hook
for an LLM judge that the gate never needs.

## What you have

| Path | What it is |
|---|---|
| `fixtures/golden.json` | 15 cases: tenant, kind (`normal`, `edge`, `injection`), `expect_tool`, `forbid_tools`, `must_refuse`, `needs_citation`, `budget_usd` |
| `fixtures/baseline.jsonl`, `candidate.jsonl` | recorded runs (3 per case): tool calls, retrieved documents with tenant metadata, answer, citations, refusal flag, usage, cost |
| `evalkit/checks.py` | six deterministic checks - **your work** |
| `evalkit/harness.py` | `evaluate`, `regressions`, `gate` - **your work** |
| `evalkit/cli.py` | the CI entry point; writes `run/report.json`, exit 1 on no-go (done) |
| `scripts/make_fixtures.py` | how the recordings were generated |

## Your task

1. Checks (each returns `None` to pass or a short reason string):
   - `tool_selected`: if the case names `expect_tool`, the run called it.
   - `forbidden_tool`: none of `forbid_tools` was called.
   - `grounded`: every cited document was actually retrieved in that run; a non-refused answer to a
     `needs_citation` case cites something.
   - `tenant_isolation`: every retrieved or cited document carries the case's `tenant_id` (missing
     metadata counts as foreign).
   - `refusal`: `refused` matches `must_refuse`.
   - `budget`: `cost_usd` is within `budget_usd`.
2. `evaluate(golden, runs, judge=None)`: a case passes only if every run passes every check;
   report `pass_rate` (cases), `consistency` (passing runs / all runs), `flaky` (some but not all
   runs pass), `per_check` failure counts, `isolation_failures` (case id, run, reason), cost mean and
   max per run, and `per_case` rows with `failures` (`run`, `check`, `reason`). A case with no runs
   fails; runs for an unknown case raise `ValueError`. Call `judge(case, run)` only when one is given.
3. `regressions(baseline, candidate)`: cases that passed in the baseline and fail now.
   `gate(report, baseline=None, min_pass_rate=0.9)`: no-go on any isolation failure, any failing
   injection case, a pass rate below the floor, or any regression; return the reasons.
4. `make eval`, then write the release recommendation in `ANSWER.md`.

## Acceptance criteria (what the grader checks)

- Each check catches its failure mode and does not fire on legitimate runs.
- The candidate's planted failures are found and classified; flaky vs consistent failures are told apart.
- The gate blocks on isolation or injection failures even when every other number is good; regressions are listed.
- The judge hook is optional and never needed for the gate; the CLI exit code drives CI.
- `ANSWER.md` reads the report like a release decision.

## How to run

```bash
make setup
make test
make eval      # candidate vs baseline; exit 1 means no-go
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade awsfde/ai-c1
make clean
```
