-- pipeline-svc schema (owned by pipeline-svc; accounts live in accounts-svc and are referenced by id only).
CREATE TABLE opportunities (
  id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tenant_id  text NOT NULL,
  account_id bigint NOT NULL,
  owner_id   text NOT NULL,
  name       text NOT NULL,
  stage      text NOT NULL CHECK (stage IN ('prospecting', 'qualification', 'proposal', 'negotiation', 'closed_won', 'closed_lost')),
  amount     numeric(14, 2) NOT NULL DEFAULT 0 CHECK (amount >= 0),
  close_date date,
  version    integer NOT NULL DEFAULT 1,
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT opportunities_closed_needs_date CHECK (stage NOT IN ('closed_won', 'closed_lost') OR close_date IS NOT NULL)
);

CREATE TABLE stage_history (
  id             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tenant_id      text NOT NULL,
  opportunity_id bigint NOT NULL REFERENCES opportunities (id),
  from_stage     text NOT NULL,
  to_stage       text NOT NULL,
  version        integer NOT NULL,
  changed_by     text NOT NULL,
  changed_at     timestamptz NOT NULL DEFAULT now()
);

-- Transactional outbox: the relay (outbox-relay) polls unpublished rows and publishes them to Kafka.
CREATE TABLE outbox (
  event_id       uuid PRIMARY KEY,
  tenant_id      text NOT NULL,
  aggregate_type text NOT NULL,
  aggregate_id   text NOT NULL,
  type           text NOT NULL,
  payload        jsonb NOT NULL,
  created_at     timestamptz NOT NULL DEFAULT now(),
  published_at   timestamptz
);
CREATE INDEX outbox_unpublished_idx ON outbox (created_at) WHERE published_at IS NULL;

CREATE ROLE pipeline_app NOLOGIN NOBYPASSRLS;
GRANT SELECT, INSERT, UPDATE ON opportunities, stage_history TO pipeline_app;
GRANT INSERT ON outbox TO pipeline_app;

DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['opportunities', 'stage_history', 'outbox'] LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', t);
    EXECUTE format($p$CREATE POLICY tenant_isolation ON %I
                     USING (tenant_id = current_setting('app.tenant_id', true))
                     WITH CHECK (tenant_id = current_setting('app.tenant_id', true))$p$, t);
  END LOOP;
END $$;
