-- KPI views over the transformed contact rows (must also run on Athena; see README).
-- Inputs: table contacts (one row per transformed record), table agent_staffing(agent_username, dt, staffed_seconds).

CREATE OR REPLACE VIEW queue_daily AS
SELECT
  dt,
  queue_name,
  COUNT(*) AS offered,
  SUM(CASE WHEN answered THEN 1 ELSE 0 END) AS answered,
  SUM(CASE WHEN abandoned THEN 1 ELSE 0 END) AS abandoned,
  ROUND(CAST(SUM(CASE WHEN answered AND queue_seconds <= 60 THEN 1 ELSE 0 END) AS DOUBLE) / COUNT(*), 4) AS service_level_60s
  -- TODO: short_abandons, abandon_rate, avg_handle_seconds; service level definition (README)
FROM contacts
WHERE queue_name IS NOT NULL
GROUP BY dt, queue_name;

-- TODO: agent_occupancy, containment_by_intent (README)
