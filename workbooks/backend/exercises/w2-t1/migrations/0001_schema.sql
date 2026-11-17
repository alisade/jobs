-- pipeline-svc / accounts-svc shared schema (excerpt relevant to the timeline).
CREATE TABLE accounts (
  id         uuid PRIMARY KEY,
  tenant_id  text NOT NULL,
  name       text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE activities (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tenant_id   text NOT NULL,
  account_id  uuid NOT NULL REFERENCES accounts (id),
  type        text NOT NULL,
  subject     text NOT NULL,
  occurred_at timestamptz NOT NULL
);

-- Added in 2026.31 for the account timeline (keyset pagination, newest first).
CREATE INDEX activities_account_timeline_idx ON activities (tenant_id, account_id, occurred_at DESC, id DESC);
