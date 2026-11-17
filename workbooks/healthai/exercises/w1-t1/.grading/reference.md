# Reference: healthai/w1-t1

Root cause: `clockreport/deadlines.py`. `add_days(start, days, business=True)` came from the legacy UM
toolkit, where a state commercial rule used working days. `decision_deadline` calls
`add_days(local, STANDARD_DAYS)` and silently inherits business days. Seven business days is at least nine
calendar days, and every late standard case in the export was decided between day 7 and day 9, so the
report showed 0 late. Fixed: `business=False` (better: make `business` keyword-only with no default).

Numbers on the fixed seed: standard late 0 -> 21 of 374; expedited late 7 of 111 before and after (the
72-hour path never used `add_days`). Audit sample: PA-2026-00201, -00419, -00592, -00606, -00611 all late.

Red herring: the DST warning fires when the UTC offset differs between receipt and the due date. The
code preserves the local time of day, which is the intended reading of "7 calendar days"; it changes
the elapsed hours by one, not the day.

Impact: the reviewer queue's time-remaining column used the same function, so nurses saw two to four
extra days on standard cases. Prevention: rule-text-driven table tests, no defaulted booleans for
regulatory semantics, a second independent calculation in the publish pipeline, compliance owns the
interpretation document.
