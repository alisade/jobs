# Rubric: connect/w4-t1 Wave 2 parallel run fails migration validation
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh (several rows are guards that already pass on the starter) |
| 2 | Root cause identified | 25 | Full: HelpDeskHours was created with TimeZone UTC, so its 06:00-20:00 window is evaluated in UTC (02:00-16:00 EDT): calls 16:00-20:00 ET hit the closed branch and 02:00-06:00 ET reach the menu; the holiday hours resource is America/New_York, which is why holiday cases pass. Partial (10-15): "hours are wrong / shifted" without naming the time zone, or names UTC without explaining both symptom windows. Zero: blames the translated flow, the routing profile change or the holiday overrides. |
| 3 | Evidence | 20 | Full: at least two independent pieces quoted: report FAIL rows clustered at 02:00-06:00 and 16:00-20:00 NY time; flow log `CheckHoursOfOperation ... Results False` at 20:40Z (16:40 ET) on hoo-helpdesk; CTRs with CONTACT_FLOW_DISCONNECT after ~19 s from 20:40Z on vs agent-handled calls before 20:00Z; the config line. Partial: one piece. Zero: assertion only. |
| 4 | Red herring handled | 5 | Rules out the routing profile delay change (only affects agent selection between queues in RP-VIPDesk, cannot produce a closed prompt or reach a menu at 03:10) with that reason. |
| 5 | Fix quality | 10 | TimeZone set to America/New_York (IANA, DST aware). No fixed offset (Etc/GMT+4 or "EST"), no shifting the hours to UTC times, no flow edits, no removal of the hours check. |
| 6 | Prevention / production | 10 | Concrete: lint that every hours resource uses the site's IANA zone; validation suite in CI with DST transition dates and holidays; explain the review gap (the flow was right; config is a separate artifact the factory did not compare); test calls across the full 24 h before porting. Partial: generic "add tests". |
Total: 100
