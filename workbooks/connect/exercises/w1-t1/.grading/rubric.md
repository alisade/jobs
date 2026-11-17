# Rubric: connect/w1-t1 "All specialists are busy" on repeat
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: two parts, both named: (a) the Check staffing block has an explicit QueueId pinned to PasswordReset (latent since 2026.09.30, so VIP/General/outage paths were checking the wrong team), and (b) CHG-48211 sent set-q-overflow back into that same block, creating an unbounded cycle that only spins when PasswordReset has 0 staffed (training from 14:00). Partial (10-15): only the loop or only the pinned QueueId. Zero: Okta, Lambda, capacity. |
| 3 | Evidence | 20 | Full: flow log excerpts showing check-staffing -> overflow-msg -> set-q-overflow -> check-staffing repeating with QueueId = q-password-reset and Results False; CTR counts (CUSTOMER_DISCONNECT with no queue) starting at 14:00; staffing CSV showing PasswordReset 0 at 14:00-15:30; explains why ContactFlowErrors stayed 0 (a loop is not an error). Partial: one piece. |
| 4 | Red herring handled | 5 | Okta 429s ruled out: retries succeeded, Lambda Errors/Throttles 0, option 2/3/VIP callers loop without ever invoking the reset Lambda. |
| 5 | Fix quality | 10 | Staffing checks the working queue (no pinned QueueId), the overflow re-check is bounded (separate check or Loop) and ends in a message + disconnect or callback, intent of CHG-48211 kept; no blanket removal of the staffing check. |
| 6 | Prevention | 10 | Concrete: graph lint (unbounded cycles) and staffing-matrix simulation tests in CI, Connect test cases (test designer / StartTestCaseExecution) in the pipeline, an alarm on calls with no queue and short duration (CTR stream), flow log metric filter on repeated identifiers per contact. Partial: generic "more testing". |
Total: 100
