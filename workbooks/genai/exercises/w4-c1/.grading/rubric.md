# Rubric: genai/w4-c1 Paired bias probes for the gift recommender
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Statistical reasoning | 15 | Full: explains why pairing removes between-prompt variance, why the aggregate over four categories dilutes a one-category gap ($28 in 1 of 4 categories is about $7 overall, under the $10 threshold), why a permutation test needs no normality assumption, and notes multiple comparisons (18 cells at alpha 0.05) with a sensible response (Holm or Bonferroni, or a pre-registered primary cell, or re-run to confirm). Partial: correct but shallow. |
| 3 | Metric design | 10 | Price from structured output, refusals excluded from price but counted in refusal rate, tone kept as report-only with its weakness stated, missing and malformed data reported rather than silently dropped. |
| 4 | System card paragraph | 15 | States the finding in plain words, with the size, CI and p, and says what Kestrel will do (mitigation, re-test, owner). Covers the limits: names are a proxy for demographic groups, only 2 dimensions were tested, results depend on sampling temperature. Readable by a product owner. Partial: numbers without action, or action without numbers. |
| 5 | Production notes | 10 | The gate runs on every prompt or model change. Explains what happens on failure (block, triage, mitigation such as removing the name from the context the recommender sees, then re-test). Probe set versioning, more samples per probe, adding dimensions (age, gender cues, location). |
Total: 100
