-- Q2 Weekly average handle time per channel.
-- Output: week_start DATE (local Monday), channel VARCHAR, aht_seconds DOUBLE rounded to 1 decimal.
-- AHT = interaction + after-contact work, over contacts that reached an agent. Order: week_start, channel.
SELECT
  CAST(date_trunc('week', timezone('America/New_York', initiation_timestamp)) AS DATE) AS week_start,
  channel,
  ROUND(AVG(agent_interaction_duration_s + after_contact_work_duration_s), 1) AS aht_seconds
FROM contact_records
GROUP BY ALL
ORDER BY week_start, channel;
