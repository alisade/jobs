# ANSWER: connect/w4-t1 Wave 2 parallel run fails migration validation

## Approach

Read the PAGE, then grouped the FAIL rows in incident/validation-report.txt by New York time:
every failure is 02:00-05:30 or 16:00-19:30 NY, holidays all pass. That pattern is a 4 hour
shift, which pointed at time evaluation rather than flow logic. Checked the flow logs, CTRs and
the hours config, then ruled out the routing profile change.

## Root cause

HelpDeskHours (hoo-helpdesk) was exported with "TimeZone": "UTC". Connect evaluates hours in the
resource's own zone, so 06:00-20:00 UTC = 02:00-16:00 EDT, while vector 14 checks
"time-of-day is all 20:00 to all 06:00" on the CM clock (America/New_York).

- report: `FAIL 2026-10-09T06:00:00.000Z (NY 02:00 FRI) legacy: Disconnected | connect: Queued GeneralSupport`
  and `FAIL 2026-10-09T20:00:00.000Z (NY 16:00 FRI) legacy: Queued ... | connect: Disconnected`.
- flow log 7f3c2a10...: `CheckHoursOfOperation step-02-goto Results False HoursOfOperation .../hoo-helpdesk`
  at 2026-10-09T20:40:03Z = 16:40 ET.
- CTRs: from 20:40Z (16:40 ET) every call is CONTACT_FLOW_DISCONNECT after 18-19 s; 19:30Z (15:30 ET)
  reached q-password-reset; 07:10Z (03:10 ET) queued in q-general-support for 15 minutes.
- HelpDeskHolidays uses America/New_York, which is why Columbus Day cases pass.

Red herring: release 2026.10.08 changed RP-VIPDesk's delay for q-general-support. Routing profile
delay only affects which queue an agent in that profile is offered; it cannot change a flow branch.

## Fix

config/hours-of-operation.json: HelpDeskHours TimeZone -> "America/New_York". `make validate`:
10/09, 10/12, 10/13 -> MISMATCH 0; `make validate DATES=2026-11-02,2026-03-09,2026-11-26` -> 0.
A fixed offset (Etc/GMT+4) still fails 2026-11-02, so it must be the IANA zone. make test green.

## Trade-offs / what I would do in production

The factory reviewed the flow, but the bug was in a separate artifact. Add a config lint (all
hours resources in the site's IANA zone), run this validation suite in CI with DST and holiday
dates, and make 24-hour synthetic test calls part of the port gate.
