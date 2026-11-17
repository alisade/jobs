# backend/x-2 - The migration that took the API down

**Type:** troubleshooting | **Estimate:** 2 hours | **Study plan:** Week 7 add-on (Mon: zero-downtime migrations); Week 2 (Fri: MVCC, isolation and locks)

## Scenario

Keystone release 2026.46 shipped migration `0057_activities_contact_fk.sql` (KEY-2533): a foreign key
from `activities` to `contacts` and an index for the contact timeline. In staging it ran in four
seconds. In production, at 02:00 UTC in the maintenance window, accounts-svc and the timeline API
returned 503s for eleven minutes. The database was nearly idle the whole time. On call raised the
connection pool and restarted pods, which changed nothing, then killed the migration backend and
everything recovered at once. The post-incident review is tomorrow and the migration still has to ship.

## What you have

| Path | What it is |
|---|---|
| `evidence/TIMELINE.md` | incident timeline |
| `evidence/pg_stat_activity.txt` | sessions at 02:08, with `pg_blocking_pids` and three settings |
| `evidence/pg_locks.txt` | relation locks on `activities` and `contacts` at 02:08 |
| `evidence/accounts-svc.log`, `migration-job.log`, `metrics.txt` | app, migration job and database metrics |
| `migrations/` | `0001_baseline.sql` (squashed history) and the `0057` that caused the incident |
| `scripts/migrate.js` | Lumenfold's runner `kmigrate`, reproduced for PGlite: one transaction per file unless the file starts with `-- kmigrate:no-transaction` |
| `scripts/lint.js` | `kmigrate-lint`, the checks the team adopted after the incident (do not weaken it; the grader uses its own copy) |
| `scripts/seed.sql` | synthetic data loaded after the baseline |

PGlite is real PostgreSQL 18 but a single session, so the lock wait itself cannot be replayed here;
that is what the captured `pg_locks` and `pg_stat_activity` evidence is for. The end state of your
migrations is checked on PGlite for real.

## Your task

1. Find the root cause from the evidence. Explain which session held which lock, which lock the
   migration requested, why every API query then waited, and why staging did not show it.
2. Replace `0057` with safe migrations (you may add `0058`, `0059`, ...; keep `0001` unchanged):
   `lock_timeout` (and a `statement_timeout`) before DDL; the FK added `NOT VALID` and validated in a
   later migration; the index built `CONCURRENTLY` in its own no-transaction migration.
3. `make lint` must be clean and `make migrate` must end with a validated FK and a valid index.
4. Fill in `ANSWER.md`: root cause with evidence, why raising the pool did nothing, the fix, and what
   you would change in the platform (deploy pipeline, reporting role settings, alerts) so it cannot
   happen again.

## Acceptance criteria (what the grader checks)

- The reference linter reports no errors, and the NOT VALID constraint is validated.
- Migrations apply in order on a fresh seeded database; `activities_contact_fk` exists, is validated and
  rejects a cross-tenant contact; an index on `(tenant_id, contact_id)` exists and is valid.
- The FK is added NOT VALID with a lock_timeout; VALIDATE is in a different migration; the index is
  CONCURRENTLY in a `-- kmigrate:no-transaction` file.
- `ANSWER.md`: root cause and evidence carry most of the points.

## How to run

```bash
make setup      # links the shared toolchain
make lint       # kmigrate-lint over migrations/
make migrate    # fresh PGlite database: baseline, seed, your migrations, then the FK and index state
make test       # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade backend/x-2
make clean
```
