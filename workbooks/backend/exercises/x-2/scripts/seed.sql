-- Synthetic data loaded after the baseline (the prod table has ~30M activities; this has 40k).
INSERT INTO accounts (tenant_id, name)
SELECT (ARRAY['bu-amer','bu-emea','bu-apac'])[1 + g % 3], 'Account ' || g FROM generate_series(1, 3000) g;
INSERT INTO contacts (tenant_id, account_id, email)
SELECT a.tenant_id, a.id, 'c' || g || '@example.test' FROM generate_series(1, 9000) g JOIN accounts a ON a.id = 1 + g % 3000;
INSERT INTO activities (tenant_id, account_id, contact_id, type, subject, occurred_at)
SELECT c.tenant_id, c.account_id, CASE WHEN g % 4 = 0 THEN NULL ELSE c.id END, 'call', 'Activity ' || g,
       timestamptz '2026-11-01' - (g || ' minutes')::interval
FROM generate_series(1, 40000) g JOIN contacts c ON c.id = 1 + g % 9000;
ANALYZE;
