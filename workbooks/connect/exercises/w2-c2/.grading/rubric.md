# Rubric: connect/w2-c2 Routing simulator: tune the LFG routing design
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Simulator design | 10 | Full: clear per-second phases, next-event time skipping, no per-second loop over idle time, pure function with no input mutation. Partial: correct but O(T x agents x contacts) or mutates inputs. |
| 3 | Routing reasoning | 15 | Full: ANSWER.md explains why the baseline fails (apps and VIP agents pulled into general at equal or higher priority with no delay, SAP contacts stuck on a step only the apps team meets, VIP sharing priority 1 with general) and maps each change to Connect: queue priority within a routing profile, delay as overflow, dedicated-first then shared. Partial: changes listed without causes. |
| 4 | Robustness check | 10 | Full: reports at least two other seeds or a +10% volume run and says whether the design still holds, with a recommendation (e.g. add 2 general agents or shorten criteria step 1). Partial: mentions robustness without numbers. |
| 5 | Model limits | 10 | Full: names what the model ignores that matters (ACW, agent statuses and breaks, voice/chat concurrency, callbacks, cross-region routing) and how to validate in Connect (historical and real-time metrics, Connect forecasting and agent scheduling). Partial: generic. |
| 6 | Code quality | 5 | Typed, small functions, comparator readable, no dead code. |
Total: 100
