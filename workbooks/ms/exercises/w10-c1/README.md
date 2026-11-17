# ms/w10-c1: Agent release gate for the Fabrikam support agent

Type: coding. Estimate: 2-3 h. Exam: AB-100 - Deploy AI-powered business solutions (40-45%): testing, and monitor, analyze and tune agents.

## Scenario

Fabrikam Home sells small kitchen appliances. Its customer-service agent (Copilot Studio, generative
orchestration) has three tools - `GetOrderStatus`, `StartReturn`, `CheckWarranty` - and three
knowledge sources: `kb:returns-policy`, `kb:warranty-terms`, `kb:shipping-faq`.

Last sprint a maker switched on a web-search knowledge source and rewrote the agent instructions
"to sound friendlier". Nobody can say whether the new version is better or worse, so the release
was paused. The CoE wants a release gate in the ALM pipeline: run the evaluation test set against
the candidate, compare it with the current production baseline, and block the deployment unless the
candidate meets absolute thresholds AND does not regress.

You get two recorded evaluation runs (`data/runs/baseline`, `data/runs/candidate`), the test set
(`data/testset.jsonl`) and the gate policy (`gate.yaml`). You build the evaluator.

How this maps to the Microsoft stack (no cloud calls in this exercise):

- **Copilot Studio agent evaluation**: test sets of test cases (question, expected response),
  several test methods per test set, results with transcript and activity map per case. Runs can
  be triggered through the Power Platform REST APIs or connector actions, which is how you would
  wire them into a CI/CD release gate like this one.
- **Microsoft Foundry agent evaluators**: Tool Selection / Tool Call Accuracy (process evaluation),
  Task Adherence, Intent Resolution, Groundedness (system/RAG evaluation). Our `tool_accuracy` and
  `grounded_rate` are code-graded cousins of those LLM-judged evaluators.
- **Application Insights**: Copilot Studio agent telemetry lands in `customEvents`; the
  `designMode` custom dimension separates test-canvas traffic from real users. Latency p95 in
  production would come from there; here it comes from transcript timestamps.

## Data formats (simplified)

`data/testset.jsonl`, one test case per line:

```json
{"id": "ret-01", "category": "returns", "utterance": "How many days ...?",
 "expected_tool": null, "allowed_sources": ["kb:returns-policy"], "must_refuse": false,
 "expected_facts": ["30 days"], "tags": []}
```

`data/runs/<run>/transcripts.jsonl`, one conversation per line. This is a simplified export,
modeled on the activity stream you see in a Copilot Studio transcript (real transcripts in the
Dataverse ConversationTranscript table carry far richer plan-step events):

```json
{"conversationId": "...", "testCaseId": "ord-01", "activities": [
  {"type": "message", "from": {"role": "user"}, "timestamp": "2026-12-15T14:00:00.000Z", "text": "..."},
  {"type": "event", "name": "toolInvoked", "timestamp": "...", "value": {"tool": "GetOrderStatus"}},
  {"type": "message", "from": {"role": "bot"}, "timestamp": "...", "text": "...",
   "entities": [{"type": "citation", "source": "kb:returns-policy"}]}]}
```

Expect dirty data: the candidate export contains a truncated line and is missing a conversation.

## Metric definitions (the tests follow these exactly)

Per test case, using the transcript whose `testCaseId` matches. "Final answer" = the LAST bot
message; its citations = its `entities` with `type == "citation"`. Text matching uses
`normalize()` (lowercase, non-alphanumerics to single spaces) and whole-word containment
(`" " + needle + " "` in `" " + haystack + " "`).

| Result key | Applies when | Value |
|---|---|---|
| `tool_correct` | `expected_tool` set | the FIRST `toolInvoked` event's tool == expected_tool |
| `grounded` | `allowed_sources` non-empty | final answer has >= 1 citation and every citation is allowed |
| `refused` | transcript present | final answer contains a refusal marker from `gate.yaml` |
| `refusal_correct` | `must_refuse` | refused AND no tool invoked |
| `fact_recall` | `expected_facts` non-empty | fraction of facts found in the final answer |
| `latency_ms` | transcript present | last bot message ts minus first user message ts; None if any of those timestamps is missing/unparseable |
| `passed` | always | every applicable check above true, fact_recall == 1.0, and not an over-refusal |

Not applicable = `None`. `missing` = True when no transcript exists for the case.

**Missing transcripts are failures, not skips**: every applicable check is False and
fact_recall is 0.0. They are excluded only from `over_refusal_rate` and latency.

Run metrics (`None` when no case applies):

- `tool_accuracy`, `grounded_rate`, `refusal_recall`: mean of the boolean per-case values.
- `over_refusal_rate`: refused / (present transcripts of cases with must_refuse false).
- `fact_recall`: mean of per-case fact_recall (macro average).
- `latency_p95_ms`: nearest-rank p95 (`sorted[ceil(0.95 * n) - 1]`) over non-None latencies.

Run report from `evaluate_run`: `{"run", "cases": {id: result}, "metrics", "categories":
{name: {"cases", "passed", "pass_rate"}}, "missing": [sorted ids], "errors": [str]}`.
`categories` contains every category in the test set AND every category named in `gate.yaml`
(an empty one has `cases: 0, passed: 0, pass_rate: None`). Loader problems (invalid JSON, missing
`testCaseId` or `activities`, duplicates - keep the first, missing file) and transcripts for
unknown test-case ids are each one entry in `errors`.

## Gate rules

`compare_runs(baseline, candidate, config)` returns `deltas` (candidate minus baseline per metric,
None if either side is None), `regressions` and `case_regressions`:

- Only metrics listed under `regression:` are checked. Rates: regression when the change in the
  bad direction is strictly greater than the tolerance. `latency_p95_ms`: regression when
  candidate > baseline * (1 + tolerance). A metric that had a value in the baseline and is None in
  the candidate is a regression. Ties are never regressions.
- `case_regressions`: sorted ids that passed in the baseline and fail in the candidate.

`gate(candidate, comparison, config)` returns `{"passed", "reasons"}`. It fails for: any
`thresholds` entry not met (`min_x`: value >= limit, `max_x`: value <= limit, inclusive; a None
metric fails its threshold), any category in `categories:` with no cases or a pass rate below its
floor, more malformed records than `max_malformed_records`, any metric regression, and any case
regression in a category listed in `block_case_regressions_in`. `comparison` may be None (no
baseline). One human-readable reason per failure.

CLI: `python -m release_gate --testset ... --candidate DIR [--baseline DIR] --config gate.yaml
--out report.json` writes `{"candidate", "baseline", "comparison", "gate"}` (None where not run),
prints the verdict, exits 0 on pass, 1 on gate failure, 2 when the test set or config cannot be
read.

## Your task

1. Implement the TODOs in `release_gate/evaluate.py` (`model.py` is provided).
2. Run `make gate` and decide: ship or not? Write the decision and the top reasons in `ANSWER.md`,
   plus what you would change in the gate itself before trusting it in production.

## Acceptance criteria

- `make test` passes; the hidden tests check every rule above, including dirty data.
- The baseline passes the gate on its own; the candidate fails it for the right reasons.
- No exceptions on malformed input; the CLI exit codes match the contract.
- `ANSWER.md` explains the release decision and the limits of code-graded evaluation versus
  LLM-judged evaluators (compare meaning, groundedness) and production telemetry.

## How to run

```
make setup     # uv sync
make test      # visible tests
make gate      # run the gate on the recorded runs, writes report.json
make clean
```

## What to submit

Your `release_gate/evaluate.py` and a filled-in `ANSWER.md`. Then `/grade ms/w10-c1`.

## Study guide links

- [Week 10 - Design and Deploy (Thu: testing, Wed: monitor and tune)](../../../../microsoft-adf-powerapps-study-plan.html#week10)
- [About agent evaluation (Copilot Studio)](https://learn.microsoft.com/en-us/microsoft-copilot-studio/analytics-agent-evaluation-intro)
- [Foundry agent evaluators](https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/agent-evaluators)
- [Agent-level telemetry with Application Insights](https://learn.microsoft.com/en-us/microsoft-copilot-studio/advanced-bot-framework-composer-capture-telemetry)
- [Module: Manage testing of AI-powered business solutions](https://learn.microsoft.com/en-us/training/modules/manage-testing-ai-powered-business-solutions/)
- [Module: Monitor, analyze, and tune AI agents](https://learn.microsoft.com/en-us/training/modules/analyze-monitor-tune-ai-powered-business-solutions/)
