-- Athena-portable KPI views over the transformed contact rows.
-- Inputs: table contacts (one row per transformed record), table agent_staffing(agent_username, dt, staffed_seconds).

-- Daily queue KPIs. Service level = answered within 60 s / (offered - abandoned within 5 s).
CREATE OR REPLACE VIEW queue_daily AS
SELECT
  dt,
  queue_name,
  COUNT(*) AS offered,
  SUM(CASE WHEN answered THEN 1 ELSE 0 END) AS answered,
  SUM(CASE WHEN abandoned THEN 1 ELSE 0 END) AS abandoned,
  SUM(CASE WHEN abandoned AND queue_seconds < 5 THEN 1 ELSE 0 END) AS short_abandons,
  ROUND(CAST(SUM(CASE WHEN abandoned THEN 1 ELSE 0 END) AS DOUBLE) / COUNT(*), 4) AS abandon_rate,
  ROUND(
    CAST(SUM(CASE WHEN answered AND queue_seconds <= 60 THEN 1 ELSE 0 END) AS DOUBLE)
    / NULLIF(COUNT(*) - SUM(CASE WHEN abandoned AND queue_seconds < 5 THEN 1 ELSE 0 END), 0), 4) AS service_level_60s,
  ROUND(AVG(CASE WHEN answered THEN handle_seconds END), 1) AS avg_handle_seconds
FROM contacts
WHERE queue_name IS NOT NULL
GROUP BY dt, queue_name;

-- Agent occupancy = handle time / staffed time, per agent per day.
CREATE OR REPLACE VIEW agent_occupancy AS
SELECT
  s.dt,
  s.agent_username,
  COALESCE(h.contacts, 0) AS contacts,
  COALESCE(h.handle_seconds, 0) AS handle_seconds,
  s.staffed_seconds,
  ROUND(CAST(COALESCE(h.handle_seconds, 0) AS DOUBLE) / NULLIF(s.staffed_seconds, 0), 4) AS occupancy
FROM agent_staffing s
LEFT JOIN (
  SELECT dt, agent_username, COUNT(*) AS contacts, SUM(handle_seconds) AS handle_seconds
  FROM contacts WHERE answered GROUP BY dt, agent_username
) h ON h.dt = s.dt AND h.agent_username = s.agent_username;

-- Self-service containment by bot intent.
CREATE OR REPLACE VIEW containment_by_intent AS
SELECT
  COALESCE(lex_intent, 'none') AS lex_intent,
  COUNT(*) AS contacts,
  SUM(CASE WHEN contained THEN 1 ELSE 0 END) AS contained,
  ROUND(CAST(SUM(CASE WHEN contained THEN 1 ELSE 0 END) AS DOUBLE) / COUNT(*), 4) AS containment_rate
FROM contacts
GROUP BY COALESCE(lex_intent, 'none');
