-- KEY-2533: activities can name the contact's role on the activity, contact_id must point at a real
-- contact of the same tenant, and the contact timeline needs an index. Reviewed and approved 2026-11-10.
ALTER TABLE activities ADD COLUMN contact_role text;

ALTER TABLE activities
  ADD CONSTRAINT activities_contact_fk FOREIGN KEY (tenant_id, contact_id) REFERENCES contacts (tenant_id, id);

CREATE INDEX activities_contact_idx ON activities (tenant_id, contact_id);
