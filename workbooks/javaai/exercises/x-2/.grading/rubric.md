# Rubric: javaai/x-2 When will the tutor portfolio be done? Flow metrics and a Monte Carlo forecast
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 60 | points = 60 * passed / total from grade.sh |
| 2 | Communication | 20 | ANSWER.md gives the product lead ranges with confidence ("85%: by 2027-01-04; 50%: 2026-12-28"), a 4-week commitment at the low end (15 items at 85%), and what the forecast assumes. |
| 3 | Judgement | 15 | Keeps the zero week (holidays and conferences recur); names scope growth, WIP changes and item splitting as forecast breakers; re-forecasts weekly; Little's law cross-check; time-boxed spikes for uncertain AI work (tuning vs prompting) whose done depends on eval thresholds. |
| 4 | Code quality | 5 | Pure functions, the RNG injected, no hidden global state. |
Total: 100
