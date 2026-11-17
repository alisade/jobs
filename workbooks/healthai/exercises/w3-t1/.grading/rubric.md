# Rubric: healthai/w3-t1 Oncology and cardiology PAs pended for "missing diagnosis"
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 35 | points = 35 * passed / total from grade.sh |
| 2 | Root cause and evidence | 35 | Full: PA-2230 refactor made the mapper emit `T.ICD10` (WHO ICD-10, `http://hl7.org/fhir/sid/icd-10`) while the engine filters on `T.ICD10CM`; the engine therefore sees no diagnoses and pends every policy with a diagnosis rule (oncology, cardiology), while spine/knee policies have no diagnosis rule. Evidence: a Condition excerpt and the filter line; counts 81 -> 9 vs baseline 6/118. Partial: right cause without the "why only these lines" or numbers. Zero: blames the validator warning. |
| 3 | Red herring | 10 | Payer display warning shown to be non-blocking (validator warnings never route) and unrelated to diagnoses. |
| 4 | Regression test and prevention | 20 | Regression test fails on the released mapper. Prevention: contract test between mapper and engine, terminology validation in CI, re-route already pended cases and check their CMS-0057-F clocks, ICD-10 vs ICD-10-CM explained (HIPAA code set is ICD-10-CM). |
Total: 100
