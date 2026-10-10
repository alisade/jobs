-- Voice abandon rate by local half-hour interval, weekdays only, whole period.
WITH v AS (
  SELECT timezone('America/New_York', initiation_timestamp) AS local_ts, connected_to_agent_timestamp IS NULL AS abandoned
  FROM contact_records
  WHERE channel = 'VOICE'
)
SELECT
  strftime(time_bucket(INTERVAL 30 MINUTE, local_ts), '%H:%M') AS interval_start,
  COUNT(*) AS offered,
  COUNT(*) FILTER (WHERE abandoned) AS abandoned,
  ROUND(COUNT(*) FILTER (WHERE abandoned) / COUNT(*), 3) AS abandon_rate
FROM v
WHERE dayofweek(local_ts) BETWEEN 1 AND 5
GROUP BY ALL
ORDER BY interval_start;
