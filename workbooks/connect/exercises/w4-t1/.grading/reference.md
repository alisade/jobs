# Reference: connect/w4-t1

Root cause: `config/hours-of-operation.json` creates `HelpDeskHours` with `"TimeZone": "UTC"`
(the CDK construct default the factory never overrode). Connect evaluates an hours of operation
resource in its own time zone, so 06:00-20:00 UTC is 02:00-16:00 EDT (01:00-15:00 EST after
2026-11-01). The vector's `time-of-day is all 20:00 to all 06:00` runs on the CM clock
(America/New_York). Result:

- 16:00-20:00 ET: Connect says closed, vector queues -> "closed" prompts reported by Monterrey.
- 02:00-06:00 ET: Connect says open, vector says closed -> the 03:10 call reached the menu.
- Holiday cases pass because `HelpDeskHolidays` was created separately with America/New_York.

Evidence trail: report rows only at those two windows; flow log
`7f3c2a10...` shows `CheckHoursOfOperation step-02-goto Results False` on `hoo-helpdesk` at
20:40:03Z = 16:40 ET; CTRs from 20:40Z onwards end with CONTACT_FLOW_DISCONNECT after ~18-19 s
while 19:30Z (15:30 ET) reached an agent; the 07:10Z (03:10 ET) CTR queued for 15 minutes.

Red herring: the 2026-10-08 release changed RP-VIPDesk's delay on the general queue (0 -> 30 s).
Routing profile delay only governs when an agent in that profile starts receiving contacts from
that queue; it cannot change which branch a flow takes or play a closed prompt.

Fix: `"TimeZone": "America/New_York"` (IANA, DST aware). Not acceptable: a fixed offset
(`Etc/GMT+4` breaks after 2026-11-01), shifting the hours to 10:00-24:00 UTC (same DST break),
editing the flow.

Why the review missed it: the factory compared flow to vector; the bug lives in a different
artifact (hours config) that a flow diff never shows. Prevention: config lint (every hours
resource uses the site's IANA zone; no UTC for customer-facing hours), the validation suite in
CI with DST-transition dates and every holiday, and 24-hour synthetic test calls before porting.
