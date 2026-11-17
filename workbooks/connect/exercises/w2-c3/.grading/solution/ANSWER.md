# ANSWER: connect/w2-c3 Help desk KPI analytics

## Approach

Weekly volume by driver first (Q1), then FCR proxy by driver (Q3), then daily password-reset volume
and repeat rate against the change calendar (Q5).

## Root cause

CHG0031877 (Okta SSPR policy, 2026-09-21 06:00 local). Q5: password-reset contacts step from ~370/day
to ~600/day on 09-21 and the repeat rate from ~0.18 to ~0.38. Weekly: 1,813/1,887/1,889 before vs
3,009/3,191 after (+1,237/week); FCR proxy 0.815 -> 0.624 (week of 09-21). The week of 09-28 shows 0.77
only because its 7-day window runs past 2026-10-04 (right-censoring). MFA enrollment also up ~25%.

## Fix

Q1 used UTC weeks (Sunday-evening chats moved to the next week); Q2 averaged abandoned contacts; Q4
bucketed UTC hours and included weekends. Red herrings: CHG0031881, the short-staffed week, the
structural 08:00-10:00 abandon peak, CHG0031790.

## Trade-offs / what I would do in production

+1,237 contacts x ~7 min ~ 145 agent-hours/week ~ 4-5 FTE, not 12. Fix upstream: enrollment grace,
Okta Verify campaign, portal and IVR self-service reset, KB article; alarm on password-reset share.
