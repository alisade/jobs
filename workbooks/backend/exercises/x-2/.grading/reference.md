# Reference: backend/x-2 The migration that took the API down

Injected fault: `migrations/0057_activities_contact_fk.sql` runs ADD COLUMN, ADD CONSTRAINT FOREIGN KEY
(validating) and a plain CREATE INDEX in one transaction with no lock_timeout. In production a
`finance-recon` session was idle in transaction holding AccessShareLock on activities; the ADD COLUMN's
AccessExclusiveLock request waited behind it, and every API query on activities queued behind that
waiting request. The database was idle; the pool change only added waiters.

Reference migrations in `.grading/solution/migrations/` (0057 rewritten, 0058 CONCURRENTLY with
`-- kmigrate:no-transaction`, 0059 VALIDATE CONSTRAINT) and the model answer in
`.grading/solution/ANSWER.md`. The hidden tests use `.grading/tests/lint-ref.js`, an identical copy of
`scripts/lint.js`, so weakening the linter in the exercise does not help.

## Interview angles
- "Why does a waiting lock block readers that do not conflict with the holder?" (Lock requests are
  queued; a new request that conflicts with a queued one waits behind it to avoid starving the DDL.)
- "What locks do NOT VALID and VALIDATE CONSTRAINT take?" (ADD ... NOT VALID: ShareRowExclusive on both
  tables, briefly; VALIDATE: ShareUpdateExclusive on the table, RowShare on the referenced table.)
- "How do you ship DDL safely at scale?" (lock_timeout plus retries, expand/contract, CONCURRENTLY,
  linting, and tools like pgroll for long-running multi-step changes.)
