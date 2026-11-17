-- Baseline (squashed 0001-0056): the Keystone tables this incident touches.
CREATE TABLE accounts (
  id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tenant_id  text NOT NULL,
  name       text NOT NULL,
  CONSTRAINT accounts_tenant_id_id_key UNIQUE (tenant_id, id)
);
CREATE TABLE contacts (
  id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tenant_id  text NOT NULL,
  account_id bigint NOT NULL,
  email      text,
  CONSTRAINT contacts_tenant_id_id_key UNIQUE (tenant_id, id),
  CONSTRAINT contacts_account_fk FOREIGN KEY (tenant_id, account_id) REFERENCES accounts (tenant_id, id)
);
CREATE TABLE activities (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tenant_id   text NOT NULL,
  account_id  bigint NOT NULL,
  contact_id  bigint,
  type        text NOT NULL,
  subject     text NOT NULL,
  occurred_at timestamptz NOT NULL,
  CONSTRAINT activities_account_fk FOREIGN KEY (tenant_id, account_id) REFERENCES accounts (tenant_id, id)
);
CREATE INDEX activities_timeline_idx ON activities (tenant_id, account_id, occurred_at DESC, id DESC);
