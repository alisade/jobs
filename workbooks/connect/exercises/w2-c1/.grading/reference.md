# Reference: connect/w2-c1

Reference implementation: `.grading/solution/src/erlang.ts`.

- Erlang B recursion `B(k) = A B(k-1) / (k + A B(k-1))`, then
  `C = N B / (N - A (1 - B))`. Stable for thousands of agents; the factorial form overflows past
  ~170 and returns NaN (Infinity / Infinity), which silently ends the starter's search loop.
- `SL(t) = 1 - C exp(-(N - A) t / AHT)`, `ASA = C AHT / (N - A)`, occupancy `A / N`.
- Search starts at `floor(A) + 1` (a queue with N <= A never drains) and at `ceil(A / maxOcc)`.
- Shrinkage: `scheduled = ceil(agents / (1 - s))`. 14 agents at 30% shrinkage need 20, not
  `round(14 * 1.3) = 18`: shrinkage is a share of paid time, so you divide.
- Chat concurrency as slots: a reasonable planning approximation; it overstates efficiency
  because agents rarely sustain full concurrency, and handle time grows with concurrency.

Monday plan (80% in 30 s, AHT 372 s, max occupancy 85%, shrinkage 32%): peak 37 scheduled at
08:30-09:00, 295.5 scheduled agent-hours. With AHT 432 s: peak 43 (+6), 338 agent-hours (+42.5, ~14%).
A one-minute AHT increase is roughly a 14% labor increase: that is the business case for
knowledge (agent assist), screen pops and after-contact summarization.

Interview points: Erlang C ignores abandonment (overstates staff at high load; Erlang A or
simulation fixes that), assumes Poisson arrivals and independent intervals, single skill. Multi-
skill and proficiency routing need simulation (see w2-c2). Connect's forecasting and agent
scheduling produces forecasts, capacity plans and schedules; use this model to sanity-check and
to explain trade-offs to stakeholders.
