# ANSWER: backend/x-2 The migration that took the API down

## Approach

Started from `pg_blocking_pids` in `pg_stat_activity.txt` to build the wait-for chain, then matched
each pid to its granted and waiting locks in `pg_locks.txt`, then checked the settings and the timeline.

## Root cause

A lock queue behind a long-running transaction, with no `lock_timeout` on the migration.

1. `finance-recon` (pid 47102, role `reporting`) opened a transaction at 01:40:11 and was
   `idle in transaction` at 02:08, still holding `AccessShareLock` on `activities` and `contacts` (granted = t).
2. kmigrate (pid 48213) ran 0057 as one transaction. Its first statement, `ALTER TABLE activities ADD
   COLUMN contact_role text`, needs `AccessExclusiveLock` on `activities`, which conflicts with every other
   lock, including the reporting job's `AccessShareLock`. So it waited: `48213 | {47102}` and
   `activities | AccessExclusiveLock | f`. Had it got the lock, it would have held it until commit, through
   the FK validation scan and the plain `CREATE INDEX` over about 30 M rows, which is an outage on its own.
3. PostgreSQL grants locks in queue order: once the migration's request is waiting, every later request
   that conflicts with it waits behind it. AccessExclusive conflicts with everything, so every API read
   (`AccessShareLock`) and write (`RowExclusiveLock`) on `activities` queued behind the migration. `pg_blocking_pids` shows 48290, 48291,
   48297 and 236 more blocked by 48213, not by the reporting job.
4. With `lock_timeout = 0` the migration would wait forever; with `idle_in_transaction_session_timeout = 0`
   the reporting session would never be cut off. Nothing ended the chain until pid 48213 was terminated at
   02:10:41, and traffic recovered within seconds (`accounts-svc.log` 02:10:45).

Why the pool change did nothing: the connections were not busy, they were waiting on a lock. More
connections only meant more sessions in the queue (`metrics.txt`: 240 active connections, 238 waiting on
a lock, CPU 6-12%, IO idle, commits down to 2-4 per second). Staging was fast because no long-running
transaction was open there, and the table is a fraction of production's 30 M rows.

## Fix

- `0057_activities_contact_fk.sql`: `SET LOCAL lock_timeout = '3s'`, `statement_timeout = '15s'`,
  `ADD COLUMN contact_role` (metadata only, no default) and `ADD CONSTRAINT ... NOT VALID`. The lock is held for milliseconds and existing rows are not scanned; if
  the lock is not available in 3 s the migration fails and is retried instead of queueing traffic.
- `0058_activities_contact_idx.sql` (`-- kmigrate:no-transaction`): `CREATE INDEX CONCURRENTLY IF NOT
  EXISTS activities_contact_idx ON activities (tenant_id, contact_id)`; writes continue during the build;
  a failed build leaves an INVALID index that is dropped concurrently and rebuilt.
- `0059_validate_activities_contact_fk.sql`: `VALIDATE CONSTRAINT`, which takes `ShareUpdateExclusiveLock`
  on activities, so reads and writes continue during the scan.
- Verified: `make lint` prints `lint clean`; `make migrate` shows `activities_contact_fk` validated and
  `activities_contact_idx` valid; the tests pass.

## Trade-offs / what I would do in production

Run kmigrate-lint (or squawk) in CI on every migration. Make the migration job retry on lock_timeout
with backoff and alert after N attempts, rather than block. Set `idle_in_transaction_session_timeout`
(for example 5 min) and a `statement_timeout` on the `reporting` role, and move finance-recon to a
replica. Alert on `pg_stat_activity` lock waits older than 5 s and on transactions older than 15 minutes.
Before a migration, a pre-check that refuses to start while a transaction older than a few minutes is
open on the target tables.
