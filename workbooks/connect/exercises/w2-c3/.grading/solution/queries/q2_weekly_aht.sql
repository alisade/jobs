-- Weekly AHT per channel: answered contacts only, handle = interaction + after-contact work.
SELECT
  CAST(date_trunc('week', timezone('America/New_York', initiation_timestamp)) AS DATE) AS week_start,
  channel,
  ROUND(AVG(agent_interaction_duration_s + after_contact_work_duration_s), 1) AS aht_seconds
FROM contact_records
WHERE connected_to_agent_timestamp IS NOT NULL
GROUP BY ALL
ORDER BY week_start, channel;
