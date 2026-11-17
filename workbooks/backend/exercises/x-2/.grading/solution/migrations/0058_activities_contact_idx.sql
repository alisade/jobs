-- kmigrate:no-transaction
-- KEY-2533 step 2 of 3: build the index without blocking writes. Runs outside a transaction (CONCURRENTLY
-- requires it). If it fails it leaves an INVALID index: drop it (DROP INDEX CONCURRENTLY) and rerun.
SET lock_timeout = '3s';
SET statement_timeout = 0;
CREATE INDEX CONCURRENTLY IF NOT EXISTS activities_contact_idx ON activities (tenant_id, contact_id);
