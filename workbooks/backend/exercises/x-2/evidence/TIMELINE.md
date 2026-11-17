# KS-2307: accounts-svc and timeline API down for 11 minutes during the 2026.46 deploy

**When:** Thu 2026-11-12, 02:00-02:11 UTC (maintenance window, 25% of normal traffic)
**On call:** Marcus Oyelaran. **Migration author:** Priya Natarajan (KEY-2533, reviewed 2026-11-10)

| UTC | What happened |
|---|---|
| 01:40 | `finance-recon` nightly job (role `reporting`) opens its session on the primary and starts its export |
| 02:00:04 | Argo CD sync of keystone 2026.46 starts; Helm pre-upgrade hook runs `kmigrate` |
| 02:00:05 | kmigrate starts `0057_activities_contact_fk.sql` |
| 02:00:20 | accounts-svc p99 latency alarm; pool wait timeouts begin |
| 02:01 | `/healthz` failing on 6/6 accounts-svc pods (DB check times out); load balancer pulls them; 503s |
| 02:02 | CPU on the primary at 12%, IO idle. Marcus: "DB is not even busy?" |
| 02:04 | Proposal in channel: raise accounts-svc pool size 10 -> 40 and restart pods. Done at 02:06; no change |
| 02:08 | Marcus captures `pg_stat_activity` and `pg_locks` (files in this folder) |
| 02:10:41 | Marcus terminates the kmigrate backend (pid 48213); helm upgrade fails, rollout aborted |
| 02:10:45 | Traffic recovers within seconds |
| 02:11 | All pods ready. `finance-recon` still running, finishes at 02:39 |

Open question from the review: "the migration was tested in staging and took 4 seconds, why did it
take the API down in prod?" The 0057 file is in `migrations/`.
