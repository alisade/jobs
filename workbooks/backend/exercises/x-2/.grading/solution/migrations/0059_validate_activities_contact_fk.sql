-- KEY-2533 step 3 of 3: check the existing rows. VALIDATE CONSTRAINT takes SHARE UPDATE EXCLUSIVE on
-- activities (reads and writes continue) and ROW SHARE on contacts while it scans.
SET LOCAL lock_timeout = '3s';
SET LOCAL statement_timeout = '30min';
ALTER TABLE activities VALIDATE CONSTRAINT activities_contact_fk;
