-- Synthetic data: 8,000 accounts over four tenants, 160,000 activities. Account 1 ("Orbital Freight",
-- bu-emea) is the biggest customer and has 20,000 activities.
INSERT INTO accounts (id, tenant_id, name)
SELECT md5('acct' || g)::uuid, (ARRAY['bu-amer','bu-emea','bu-apac','app-partner-portal'])[1 + g % 4],
       CASE WHEN g = 1 THEN 'Orbital Freight' ELSE 'Account ' || g END
FROM generate_series(1, 8000) g;
INSERT INTO activities (tenant_id, account_id, type, subject, occurred_at)
SELECT a.tenant_id, a.id, (ARRAY['call','email','meeting','task','note'])[1 + g % 5], 'Activity ' || g,
       timestamptz '2026-11-01 00:00:00+00' - ((g / 2) || ' minutes')::interval
FROM generate_series(1, 160000) g
JOIN accounts a ON a.id = md5('acct' || (CASE WHEN g % 8 = 0 THEN 1 ELSE 1 + g % 8000 END))::uuid;
ANALYZE;
