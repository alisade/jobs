# healthai/ai-c1 - Eval gate in CI for the PA assistant

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** AI Integration (5 Evals); Week 6 Thu (evals in CI)

## Scenario

Kestrel Health Plan's (fictional) PA assistant recommends outcomes with cited policy criteria. Every
prompt, model or retrieval change goes through CI, which replays a labelled synthetic set three times
(model output varies run to run) and must fail the build on a regression. Today the gate is a
hackathon script that only checks route agreement, so a release that hallucinated quotes or
auto-finalized a denial would have passed. You write the real gate.

## What you have

| Path | What it is |
|---|---|
| `fixtures/cases.json` | 30 labelled synthetic cases: gold criteria (`C1`, `C2`) and gold route |
| `fixtures/policy.json` | policy section id -> text |
| `fixtures/runs/good/run{1,2,3}.json` | recorded outputs of the current release: raw `output` string, `latency_ms`, token counts |
| `fixtures/runs/regress_*` | five recorded regressions, one per gate (you should not need to read them to write the gate) |
| `fixtures/baseline.json` | stored baseline, tolerance and token prices |
| `evals/schema.py` | the output contract (Pydantic) |
| `evals/gates.py` | the gate you rewrite |

## Your task

`evaluate(run_dir, cases, policy, baseline)` pools every row of every run and returns
`{"runs", "gates", "passed", "cost_usd_per_run", "p95_latency_ms"}` with exactly these gates, each a dict
with at least `value`, `threshold`, `passed`:

| Gate | value | passes when |
|---|---|---|
| `schema_validity` (hard) | fraction of rows whose `output` validates against `Output` | value == 1.0 |
| `citation_support` | over criteria in valid rows: cited section exists in the policy and the quote is a case-insensitive substring of its text | Wilson lower bound (z = 1.96, also returned as `lower`) >= baseline - tolerance |
| `criteria_accuracy` | over criteria in valid rows: `met` equals the gold label for that criterion id | Wilson lower bound (`lower`) >= baseline - tolerance |
| `safety` (hard) | number of valid rows with `route == "auto"` and an outcome other than approve; list them in `violations` as `run<N>:<case_id>` | value == 0 |
| `consistency` | fraction of cases whose route is identical across all runs (an invalid row counts as its own route) | value >= baseline - tolerance |

Also: `wilson_lower(successes, n, z=1.96)` (0.0 when n == 0); `p95(values)` by nearest rank;
`cost_usd_per_run` = mean over runs of the token cost at the baseline prices (per million tokens);
`p95_latency_ms` over all rows; `summary_md(report)` = a markdown table with every gate, value, bound,
threshold and result, plus cost and latency (CI writes it to the job summary); `main()` exits 1 when any
gate fails.

## Acceptance criteria (what the grader checks)

- The good runs pass; each recorded regression trips exactly its own gate.
- Wilson, nearest-rank p95, cost and the safety violation list are exact.
- The CLI writes the summary and returns 0 or 1.

## Run

```
make setup && make test
make gate RUNS=fixtures/runs/regress_citation   # what CI would print
# fill in ANSWER.md, then: /grade healthai/ai-c1
make clean
```
