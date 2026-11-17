# INC-48390: oncology and cardiology PAs pended for "missing diagnosis"

**Reported by:** UM intake lead, 2026-11-19 10:05 ET
**Severity:** high (expedited oncology requests are among them; CMS-0057-F 72-hour clock is running)

Since Tuesday's release (2026.11.1, deployed 2026-11-17 18:00 ET) almost every oncology and cardiology
prior authorization lands in the "pended: missing diagnosis" queue. The providers did send diagnoses: the
nurses can see them in the source 278 and in the portal. Imaging for the spine and knee looks normal.
Nurses are manually re-routing cases, about 40 a day.

The platform team points at the validator, which started logging a warning on every case after the
release ("Coverage.payor[0].display is empty"), and asks whether the payer display is needed for routing.

Attached: `release-2026.11.1.md` (release notes and the relevant diff), `routes-baseline.txt` (routing
summary from the previous Monday). `make setup` replays the current pipeline into `engine-run.log`.
