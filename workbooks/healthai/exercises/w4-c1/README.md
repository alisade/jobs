# healthai/w4-c1 - PA intake graph where no denial is ever automatic

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 4 (LangGraph: state, checkpointer, interrupts)

## Scenario

Kestrel Health Plan (fictional) runs utilization management for commercial, Medicare Advantage and
Medicaid managed care members. A hackathon team built a LangGraph prototype that reads a prior
authorization (PA) request, checks coverage in the FHIR store, asks a model for a recommendation and
writes the determination. Compliance stopped the pilot on day one: the prototype copies the model's
outcome straight into the determination, so the model can deny care on its own.

The design rule from the medical director is: **the system may only recommend approval. Every denial,
every pend, every low-confidence or unparseable recommendation and every eligibility problem goes to a
nurse or medical director through a LangGraph interrupt, and the reviewer's decision and reason are
stored.** CMS-0057-F also requires a specific reason for every denial.

Cases wait days for a reviewer, so the graph is checkpointed (SQLite here, Postgres in production) and
must resume in a fresh process.

## What you have

| Path | What it is |
|---|---|
| `pa_graph/graph.py` | the prototype; you rewrite it (keep the public API) |
| `pa_graph/state.py` | `PAState` (TypedDict) with an append-only `audit` list (reducer `operator.add`) |
| `pa_graph/model.py` | `Recommendation` (Pydantic v2 contract for model output) and `ScriptedChatModel`, a stub chat model that returns recorded answers per case id |
| `pa_graph/tools.py` | `FakeFhirStore.get_coverage(member_id)` over `fixtures/fhir.json` (synthetic) |
| `fixtures/cases.json` | 12 synthetic PA requests; `fixtures/model_responses.json` the recorded model answers (some are wrong on purpose) |
| `tests/` | visible tests (`make test`) |

## Your task

Build this graph in `pa_graph/graph.py`. Node names are part of the contract (tests read
`graph.get_state(config).next`):

1. `validate` (given): missing `case_id`, `member_id` or `service`, or a priority other than
   `expedited`/`standard` -> `status: "rejected"`, end, no model call.
2. `fetch_coverage` (given) -> `check_completeness`: set `missing_info` to the subset of
   `["diagnosis code", "clinical documentation"]` that is missing.
3. Routing after `check_completeness`: coverage missing or not `active` -> `human_review` (an
   eligibility problem is a potential denial; do not call the model). Else missing info ->
   `request_info`. Else -> `assess`.
4. `request_info`: `interrupt({"type": "missing_info", "case_id", "missing"})`. The resume value is a dict
   that supplies `diagnosis_codes` and/or `documents` (append them, then go back to
   `check_completeness`), or `{"withdrawn": true}` -> `status: "withdrawn"`, end.
5. `assess`: call the model with `build_prompt(state)` and validate the content with
   `Recommendation.model_validate_json`. Invalid output must not crash the graph: store
   `recommendation: {}` and a non-empty `model_error`.
6. Auto-finalize only when the recommendation is valid, `outcome == "approve"`, `confidence >=
   approve_threshold` (default 0.85, a `build_graph` argument), and every criterion is met and cited.
   Everything else -> `human_review`.
7. `human_review`: `interrupt({"type": "review", "case_id", "priority", "reason_for_review",
   "recommendation", "model_error", "review_error"})`. `reason_for_review` is exactly one of
   `"coverage not active"`, `"model output invalid"`, `"model recommends <outcome>"`, `"low confidence"`,
   `"criterion not met"` (first that applies, in that order). The resume value is
   `{"decision": "approve"|"deny"|"pend", "reviewer": "<id>", "reason": "<text>"}`. Reviewer is required;
   deny and pend need a reason of at least 15 characters. Invalid input sets `review_error` and goes back
   to `human_review` (a new interrupt); valid input is stored in `human_decision`.
8. `finalize`: status `approved`/`denied`/`pended` from the human decision, or `approved` with
   `decided_by: "auto"` only for a qualifying recommendation. The module-level `finalize(state)` must
   **raise** if asked to finalize anything else without a human decision: it is the last line of
   defence if someone rewires the edges later.
9. Every node appends at least one `{"node": "<name>", ...}` entry to `audit`; the human_review entry
   records the reviewer.

## Acceptance criteria (what the grader checks)

- Model denials and pends, low confidence, unmet criteria, invalid or out-of-range model output and
  inactive coverage all stop at `human_review` with the right `reason_for_review`.
- Missing information interrupts at `request_info`, resumes with supplied fields, or withdraws.
- Bad reviewer input re-interrupts; good input finalizes with the reviewer recorded.
- Driving every fixture case with every reviewer answer never yields a denied or pended
  determination decided by `auto`; `finalize()` raises on an unreviewed denial.
- A case interrupted in one process resumes from a SQLite checkpoint in a new graph object without
  calling the model again; two cases on two threads never mix.

## Run

```
make setup     # shared venv (first run downloads langgraph, pydantic, pytest)
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade healthai/w4-c1
make clean
```
