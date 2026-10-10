# Rubric: connect/w2-c3 Help desk KPI analytics: find what broke first-contact resolution
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 40 | points = 40 * passed / total from grade.sh |
| 2 | Root cause and evidence | 20 | Full: CHG0031877 (Okta SSPR policy: SMS factor removed, Okta Verify push required, zero grace) on 2026-09-21; password-reset volume up ~65% (about +1,240 contacts/week) and its FCR proxy down from ~0.82 to ~0.62, with MFA enrollment also up; Q5 output quoted showing the step on 09-21. Partial: right driver, no change or no numbers. Zero: staffing or routing blamed. |
| 3 | Data judgement | 15 | Full: explains the right-censoring of the last week (no 7-day lookahead after 2026-10-04), excludes or adjusts Labor Day week, explains the Q1 UTC-week bug (late chats on Sunday evening local land in the next UTC week) and the Q2/Q4 bugs (abandons in AHT, UTC hours). Partial: some. |
| 4 | Red herrings | 10 | Rules out CHG0031881 (routing profile change the next day: affects who answers, not demand), the short-staffed week of 09-28 (abandons up slightly, not volume or repeats), the 08:00-10:00 abandon peak (structural, present all period) and CHG0031790. |
| 5 | Recommendation | 15 | Full: costed: twelve agents is roughly the excess load (1,240 x 7 min ~ 145 agent-hours/week, ~4-5 FTE at the measured AHT, not 12) and treats a symptom; recommends fixing the policy rollout (grace period, Okta Verify enrollment campaign, portal and IVR self-service reset with push, knowledge article, agent assist), measuring FCR weekly and alarming on the driver mix. Partial: recommendation without numbers. |
Total: 100
