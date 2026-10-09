# Rubric: ms/w7-c1 PCF asset tag input with validation, debounce and clean teardown
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Lifecycle correctness | 15 | Full: one code path for init/updateView config, no notify from updateView, value adopted from platform without echo, mid-edit not clobbered. Partial: works but duplicated/fragile logic. Zero: notifies from updateView or loses user input. |
| 3 | Resource hygiene | 10 | Full: handler references kept and removed, timer cleared, DOM removed in destroy. Partial: some leaks. Zero: destroy empty. |
| 4 | Manifest quality | 10 | Full: properties match IInputs with correct usage/of-type, css registered, sensible keys and version. Partial: missing pieces. Zero: invalid XML. |
| 5 | Code quality and typing | 5 | Strict types, no `any`, small focused helpers, literal prefix escaping. |
| 6 | ANSWER.md trade-offs | 10 | Full: explains why client validation is not enough (server-side rule/plug-in), debounce vs blur, packaging/ALM. Partial: generic. Zero: missing. |
Total: 100
