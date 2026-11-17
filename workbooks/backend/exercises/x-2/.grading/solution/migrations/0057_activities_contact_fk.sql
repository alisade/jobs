-- KEY-2533 (rewritten after the 2026-11-12 incident), step 1 of 3.
-- ADD COLUMN without a default is metadata only but needs ACCESS EXCLUSIVE for a moment; the FK is added
-- NOT VALID, so existing rows are not scanned and the locks are held for milliseconds. lock_timeout makes
-- the migration give up (and be retried) instead of queueing every activities query behind it.
SET LOCAL lock_timeout = '3s';
SET LOCAL statement_timeout = '15s';
ALTER TABLE activities ADD COLUMN IF NOT EXISTS contact_role text;
ALTER TABLE activities
  ADD CONSTRAINT activities_contact_fk FOREIGN KEY (tenant_id, contact_id) REFERENCES contacts (tenant_id, id) NOT VALID;
