# ANSWER: healthai/ai-c1 Eval gate in CI for the PA assistant

## Approach

Parse every row first (schema gate, hard). Only valid rows feed the criteria-level gates, so invalid
output cannot improve accuracy. Safety is a hard count with the offending rows listed. Citation support
and criteria accuracy gate on the Wilson lower bound against baseline minus tolerance; consistency is route
agreement across runs.

## Fix

The hackathon gate measured route agreement only. Now: regress_schema fails schema_validity, regress_citation
fails citation_support (0.85, bound 0.79), regress_accuracy fails criteria_accuracy, regress_safety fails on
run3:EV-008, regress_variance fails consistency (0.83). The good runs pass all five; cost per run and p95
latency are in the summary.

## Trade-offs / what I would do in production

Three runs at z = 1.96 balances cost and flakiness; track gate history to spot drift. Baseline changes go
through review by compliance. Add a calibrated LLM judge for citation support after the substring check.
Eval data is synthetic or de-identified only. Run it as a GitHub Actions job and compare with the Gen AI
evaluation service for model-based metrics.
