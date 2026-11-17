# Rubric: edgefde/ai-c1 Operator assistant on a local model
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 55 | points = 55 * passed / total from grade.sh |
| 2 | Enforcement in code | 15 | Citations checked against executed call ids, schema and enum validated by Pydantic, cloud tool list filtered in code, dispatcher allow-list; explains why prompts alone are not enforcement. |
| 3 | Loop robustness | 10 | Tool errors returned as data, never raised; retry message carries the validation error; max turns bounded; client exceptions reported as status. |
| 4 | Code quality | 5 | Small functions, typed, no global state, tools return copies. |
| 5 | Production notes | 15 | Real model choice and hardware budget, eval suite run on the real local model with accuracy and latency per answer, who owns the cloud flag, tracing (OTel GenAI spans), injection testing of alert notes. |
Total: 100
