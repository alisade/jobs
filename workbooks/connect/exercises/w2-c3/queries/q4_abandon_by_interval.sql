-- Q4 Voice abandon rate by LOCAL half-hour interval, weekdays (Mon-Fri) only, whole period.
-- Abandoned = never connected to an agent.
-- Output: interval_start VARCHAR 'HH:MM', offered BIGINT, abandoned BIGINT,
--         abandon_rate DOUBLE = ROUND(abandoned / offered, 3). Order: interval_start.
SELECT
  strftime(time_bucket(INTERVAL 30 MINUTE, CAST(initiation_timestamp AS TIMESTAMP)), '%H:%M') AS interval_start,
  COUNT(*) AS offered,
  COUNT(*) FILTER (WHERE connected_to_agent_timestamp IS NULL) AS abandoned,
  ROUND(COUNT(*) FILTER (WHERE connected_to_agent_timestamp IS NULL) / COUNT(*), 3) AS abandon_rate
FROM contact_records
GROUP BY ALL
ORDER BY interval_start;
