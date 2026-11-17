-- Keystone core schema, migration 0001 (reference solution).
-- Applied as the database owner; services connect as keystone_app. Tenancy is enforced by the
-- database: composite foreign keys keep parents and children in one tenant, and FORCEd row-level
-- security filters every query on app.tenant_id, which the services set per transaction with
-- set_config('app.tenant_id', $1, true) (SET LOCAL semantics, safe behind a transaction pooler).

CREATE TABLE tenants (
  id   text PRIMARY KEY,
  name text NOT NULL
);

CREATE TABLE accounts (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tenant_id     text NOT NULL REFERENCES tenants (id),
  name          text NOT NULL CHECK (length(btrim(name)) > 0),
  owner_id      text NOT NULL,
  sf_id         text,
  custom_fields jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(custom_fields) = 'object'),
  created_at    timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT accounts_tenant_id_id_key UNIQUE (tenant_id, id),
  CONSTRAINT accounts_tenant_sf_id_key UNIQUE (tenant_id, sf_id)
);

CREATE TABLE contacts (
  id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tenant_id  text NOT NULL REFERENCES tenants (id),
  account_id bigint NOT NULL,
  first_name text,
  last_name  text NOT NULL,
  email      text CHECK (email IS NULL OR position('@' IN email) > 1),
  sf_id      text,
  deleted_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT contacts_tenant_id_id_key UNIQUE (tenant_id, id),
  CONSTRAINT contacts_tenant_sf_id_key UNIQUE (tenant_id, sf_id),
  CONSTRAINT contacts_account_fk FOREIGN KEY (tenant_id, account_id) REFERENCES accounts (tenant_id, id)
);
-- Soft delete: uniqueness only among live rows, case-insensitive.
CREATE UNIQUE INDEX contacts_live_email_key ON contacts (tenant_id, lower(email)) WHERE deleted_at IS NULL;
CREATE INDEX contacts_account_idx ON contacts (tenant_id, account_id);

CREATE TABLE opportunities (
  id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tenant_id  text NOT NULL REFERENCES tenants (id),
  account_id bigint NOT NULL,
  owner_id   text NOT NULL,
  name       text NOT NULL,
  stage      text NOT NULL CHECK (stage IN ('prospecting', 'qualification', 'proposal', 'negotiation', 'closed_won', 'closed_lost')),
  amount     numeric(14, 2) NOT NULL DEFAULT 0 CHECK (amount >= 0),
  close_date date,
  sf_id      text,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT opportunities_closed_needs_date CHECK (stage NOT IN ('closed_won', 'closed_lost') OR close_date IS NOT NULL),
  CONSTRAINT opportunities_tenant_id_id_key UNIQUE (tenant_id, id),
  CONSTRAINT opportunities_tenant_sf_id_key UNIQUE (tenant_id, sf_id),
  CONSTRAINT opportunities_account_fk FOREIGN KEY (tenant_id, account_id) REFERENCES accounts (tenant_id, id)
);
CREATE INDEX opportunities_account_idx ON opportunities (tenant_id, account_id);
-- "My open opportunities": partial index, the predicate matches the query text exactly.
CREATE INDEX opportunities_open_by_owner_idx ON opportunities (tenant_id, owner_id, close_date, id)
  WHERE stage NOT IN ('closed_won', 'closed_lost');

CREATE TABLE activities (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tenant_id   text NOT NULL REFERENCES tenants (id),
  account_id  bigint NOT NULL,
  contact_id  bigint,
  type        text NOT NULL CHECK (type IN ('call', 'email', 'meeting', 'task', 'note')),
  subject     text NOT NULL,
  occurred_at timestamptz NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT activities_account_fk FOREIGN KEY (tenant_id, account_id) REFERENCES accounts (tenant_id, id),
  CONSTRAINT activities_contact_fk FOREIGN KEY (tenant_id, contact_id) REFERENCES contacts (tenant_id, id)
);
-- Timeline keyset: equality columns first, then the sort columns in the ORDER BY direction.
CREATE INDEX activities_timeline_idx ON activities (tenant_id, account_id, occurred_at DESC, id DESC);
CREATE INDEX activities_contact_idx ON activities (tenant_id, contact_id) WHERE contact_id IS NOT NULL;

-- Custom fields (Salesforce __c): GIN with jsonb_path_ops for @> containment.
CREATE INDEX accounts_custom_fields_gin ON accounts USING gin (custom_fields jsonb_path_ops);

-- Application role: no login (a login role is granted membership), no BYPASSRLS, no ownership.
CREATE ROLE keystone_app NOLOGIN NOSUPERUSER NOBYPASSRLS;
GRANT SELECT ON tenants TO keystone_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON accounts, contacts, opportunities, activities TO keystone_app;

DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['accounts', 'contacts', 'opportunities', 'activities'] LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', t);
    EXECUTE format($p$CREATE POLICY tenant_isolation ON %I
                     USING (tenant_id = current_setting('app.tenant_id', true))
                     WITH CHECK (tenant_id = current_setting('app.tenant_id', true))$p$, t);
  END LOOP;
END $$;
