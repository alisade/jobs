-- Weekly offered contacts by driver (local weeks, Monday start), all channels, abandons included.
SELECT
  CAST(date_trunc('week', timezone('America/New_York', initiation_timestamp)) AS DATE) AS week_start,
  contact_driver,
  COUNT(*) AS contacts
FROM contact_records
GROUP BY ALL
ORDER BY week_start, contact_driver;
