-- Keystone core schema, migration 0001.
-- Owner: accounts-svc and pipeline-svc teams. Applied as the database owner; services connect as
-- keystone_app. The column names below are the contract the services and the tests use: do not
-- rename them. See README.md for the full list of requirements.

CREATE TABLE tenants (
  id   text PRIMARY KEY,           -- 'bu-amer', 'bu-emea', ...
  name text NOT NULL
);

CREATE TABLE accounts (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tenant_id     text NOT NULL REFERENCES tenants (id),
  name          text NOT NULL,
  owner_id      text NOT NULL,
  sf_id         text,               -- legacy Salesforce 18-character Id, NULL for native records
  custom_fields jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at    timestamptz NOT NULL DEFAULT now()
  -- TODO: let child tables reference (tenant_id, id); legacy sf_id unique per tenant
);

-- TODO contacts (id, tenant_id, account_id, first_name, last_name, email, sf_id, deleted_at, created_at)
-- TODO opportunities (id, tenant_id, account_id, owner_id, name, stage, amount, close_date, sf_id, created_at)
-- TODO activities (id, tenant_id, account_id, contact_id, type, subject, occurred_at, created_at)
-- TODO constraints as business rules (README "Requirements")
-- TODO indexes for queries/*.sql
-- TODO app role keystone_app, grants, row-level security
