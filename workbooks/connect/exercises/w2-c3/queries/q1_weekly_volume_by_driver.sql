-- Q1 Weekly offered contacts by driver.
-- Output: week_start DATE (Monday of the LOCAL America/New_York week), contact_driver VARCHAR,
--         contacts BIGINT (every contact, abandoned or not, all channels). Order: week_start, contact_driver.
-- The analyst's draft below gives the steering committee slightly different numbers than the
-- Connect dashboards. Find out why and fix it.
SELECT
  CAST(date_trunc('week', initiation_timestamp) AS DATE) AS week_start,
  contact_driver,
  COUNT(*) AS contacts
FROM contact_records
GROUP BY ALL
ORDER BY week_start, contact_driver;
