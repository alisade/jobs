# Reference: javaai/x-2

`.grading/solution/kanban/forecast.py`. Numbers on the data (seed 2026, 10,000 runs, start 2026-10-26, 40 items):

- weekly throughput `[7, 4, 4, 4, 5, 0, 7, 8, 4, 3, 6, 5]` (mean 4.75)
- 50%: 2026-12-28, 85%: 2027-01-04, 95%: 2027-01-11
- items in 4 weeks at 85%: 15; cycle time p50 6 days, p85 12 days

Little's law check: throughput 57 items / 84 days = 0.68 per day; with an average WIP of about 5 that
predicts ~7.4 days, consistent with the measured cycle times. If WIP grows, cycle time grows with it.

Message to the product lead: "Based on the last 12 weeks, there is an 85% chance the 40 items are done
by 4 January and a 50% chance by 28 December. For the next 4 weeks we can commit to 15 items. If scope
grows or we start more in parallel, I will re-forecast; I update this every Monday."
