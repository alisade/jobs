# Design: ICD-10-CM code suggestion for PA intake

## Decision and summary

Ship option A (prompted large model) first. At 38,000 notes a month it costs about $183 against about $620
for the always-on LoRA endpoint, and it is better on the slice that hurts most: rare codes (F1 0.701 vs
0.488), with a third of the invalid-code rate. LoRA stays as a funded experiment for a hybrid router.

## Cost per 1,000 notes and per month

A: (2900 x $1.25 + 120 x $10) / 1e6 = $0.004825 per note = $4.83 per 1,000 = $183/month.
B: one L4 replica, $0.85 x 730 h = $620/month fixed = $16.33 per 1,000 at 38k notes; capacity 6 notes/s
(about 15M/month) so it is 0.25% utilised. Break-even: 620 / 4.825 x 1,000 = about 129k notes/month.
Training: $38 per run plus 6 engineer hours per retrain.

## Quality analysis

B wins micro F1 (0.884 vs 0.861), top-50 codes (0.931 vs 0.902), exact match and latency (p95 0.69 s vs
4.2 s). B loses macro F1 (0.741 vs 0.792) and rare codes (0.488 vs 0.701): it learned the head of the
distribution. B also emits 3.1% invalid codes and 1.8% unparseable JSON. Intake suggestions are reviewed
later, so latency buys little; a missed rare oncology code can route a case to the wrong policy.

## Architecture on Agent Platform

```text
PA graph (Cloud Run, PHI project) --SA: pa-extract--> Gemini on Agent Platform (regional, BAA-covered)
      |  Pydantic validation + check against the ICD-10-CM code file
      v
  suggestions -> nurse review UI (never a decision)
Perimeter: VPC-SC around the PHI project (Agent Platform, Healthcare API); CMEK; Data Access logs on.
Option B later: private (PSC) dedicated endpoint, vLLM, min replicas 1, same perimeter.
```

## Evaluation and release gates

Held-out synthetic set of 300 plus a rare-code slice and a new-code slice. CI gates: micro F1 >= 0.85,
rare-code F1 >= 0.68, invalid code rate <= 1% after code-file validation, parse failures <= 0.5%. Shadow
mode for two weeks against nurse-confirmed codes, then rollout. Weekly drift report of acceptance rate
per code family.

## Code-set updates and retraining

A: refresh examples and the code file before October 1, re-run the eval; codes not in the file are
dropped and logged. B: retrain on refreshed data ($38, 6 hours) and full re-eval; new codes have no
training examples, which worsens the rare-code problem, so A remains the fallback.

## PHI and compliance

Training and eval data are synthetic or produced by the Healthcare API de-identify operation, versioned
as artifacts. Only BAA-covered services see notes; no note text in logs or traces; the prompt carries only
the note and the instructions (minimum necessary), not the member record.
