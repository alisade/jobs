# Reference: connect/w2-c3

Reference queries: `.grading/solution/queries/` (also `.grading/tests/ref/`). Findings:
`.grading/solution/findings.json`.

Draft bugs: Q1 truncates the UTC timestamp to a week, so Sunday 20:00-24:00 local chats fall into the
next week (and a phantom week of 2026-10-05 appears). Q2 averages over abandoned contacts (zero
handle time), dragging AHT down by roughly the abandon rate (5-8%). Q4 buckets UTC hours and includes weekends, so the 08:00-10:00
local abandon peak shows up at 12:00-14:00.

Root cause: CHG0031877, Okta SSPR policy change at 06:00 local on Monday 2026-09-21 (SMS factor
removed, Okta Verify push required, zero enrollment grace). From that day password-reset volume
steps from ~1,860/week to ~3,100/week, MFA enrollment from ~700 to ~880, password-reset AHT rises
(300 -> 420 s by design of the data) and the 7-day repeat rate for answered password-reset contacts
goes from ~18% to ~38% (FCR proxy 0.815 -> 0.624). Week 2026-09-28 looks better (FCR ~0.77) only
because its 7-day lookahead runs past the end of the data on 2026-10-04: right-censoring.

Note the pre-change repeat rate is already ~18%, higher than the "true" generated repeat rate,
because with 14,000 employees some coincidental same-driver contacts within 7 days are expected;
a strong answer notices the baseline is not zero and compares deltas.

Red herrings: CHG0031881 (routing profile, 09-22) changes who answers, not what arrives; the week of
09-28 has 10% fewer staffed agents (abandons up ~2 points, volume unchanged); the 08:00-10:00 abandon
peak exists for the whole period; CHG0031790 (ServiceNow patch) has no signal.

Recommendation: the excess is ~1,240 contacts/week x ~7 min = ~145 agent-hours, about 4-5 FTE, not
12; the right fix is upstream: restore a short enrollment grace period, run an Okta Verify enrollment
campaign, push SSPR via the portal and an IVR self-service path (identify + push verification),
publish a knowledge article and an agent-assist answer, then watch the driver mix and the FCR proxy
weekly with an alarm on password-reset share.
