# Rubric: connect/w2-c1 Erlang C staffing calculator
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Numerical soundness | 15 | Full: Erlang B recursion (or log-space) with no overflow path, explicit unstable-queue and zero-load handling, search starts above the load and respects the ceiling. Partial: correct values but relies on clamping NaN or try/catch. Zero: factorial/power implementation kept. |
| 3 | Planning semantics | 10 | Full: occupancy cap applied to servers, concurrency as slots then ceil to agents, shrinkage divides (agents / (1 - s)) not multiplies, validation with clear messages. Partial: one of these wrong but explained. |
| 4 | Answers with numbers | 10 | Full: Monday peak 37 scheduled, 295.5 scheduled agent-hours, and the AHT 432 s what-if: peak 43 scheduled (+6), 338 agent-hours (+42.5, about +14%). Partial: numbers without method. Zero: missing. |
| 5 | Limits of the model | 10 | Full: names at least three: no abandonment (Erlang A), infinite patience and no retrials, Poisson arrivals and interval independence, single skill (multi-skill/proficiency routing needs simulation), chat concurrency is an approximation, shrinkage is not occupancy; says how Connect forecasting and agent scheduling fits. Partial: one or two. |
| 6 | Code quality | 5 | Pure functions, typed, small, no duplicated math, no dead code. |
Total: 100
