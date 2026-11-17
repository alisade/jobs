# Rubric: healthai/x-1 Design: LoRA-tuned small model vs prompting for ICD-10-CM extraction
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 0 | Design exercise: grade.sh reports 0/0; this row does not apply. |
| 2 | Cost arithmetic | 20 | Prompted: (2900 x 1.25 + 120 x 10) / 1e6 = $0.004825 per note, about $4.83 per 1,000, about $183/month. Endpoint: $0.85 x 730 h = about $620/month regardless of volume (about $16.33 per 1,000 at 38k). Break-even about 129k notes/month. Notes the endpoint has huge spare capacity (6 notes/s). Partial: right method, arithmetic slips. |
| 3 | Decision follows from the evidence | 25 | Full: ships the prompted model first (cheaper at this volume, better on rare codes and macro F1, lower invalid/parse rates, no GPU endpoint to run), keeps LoRA as the option for higher volume or latency needs, or a hybrid (LoRA for top-50 codes, prompted fallback for rare or low-confidence). Must address that missed rare codes are the costly error here. Zero: picks LoRA on micro F1 and latency alone. |
| 4 | Architecture inside the boundary | 20 | Private endpoint (PSC) in the PHI project, VPC-SC perimeter, CMEK, Data Access audit logs, service account per caller, Pydantic validation plus validation against the official code file, suggestions only (nurse confirms), diagram present. |
| 5 | Evaluation and lifecycle | 20 | Held-out and sliced evals (rare codes, new codes), thresholds and a CI gate, shadow mode before rollout, drift monitoring, October 1 update plan (prompt + code-file validation for A; retrain and re-eval for B with time and cost). |
| 6 | PHI and compliance | 15 | Training on synthetic or Healthcare-API de-identified notes, provenance kept, BAA-covered services only, no PHI in logs or eval sets, minimum necessary context in the prompt. |
Total: 100
