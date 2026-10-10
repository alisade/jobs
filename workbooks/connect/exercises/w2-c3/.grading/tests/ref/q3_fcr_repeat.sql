-- First-contact resolution proxy: an answered contact is "repeated" when the same employee contacts
-- again about the same driver (any channel, answered or not) within 7 days after it started.
WITH answered AS (
  SELECT contact_id, employee_id, contact_driver, initiation_timestamp,
         CAST(date_trunc('week', timezone('America/New_York', initiation_timestamp)) AS DATE) AS week_start
  FROM contact_records
  WHERE connected_to_agent_timestamp IS NOT NULL
),
flagged AS (
  SELECT a.week_start, a.contact_driver,
         EXISTS (
           SELECT 1 FROM contact_records n
           WHERE n.employee_id = a.employee_id
             AND n.contact_driver = a.contact_driver
             AND n.initiation_timestamp > a.initiation_timestamp
             AND n.initiation_timestamp <= a.initiation_timestamp + INTERVAL 7 DAY
         ) AS repeated
  FROM answered a
)
SELECT week_start, contact_driver,
       COUNT(*) AS answered_contacts,
       COUNT(*) FILTER (WHERE repeated) AS repeat_within_7d,
       ROUND(1 - COUNT(*) FILTER (WHERE repeated) / COUNT(*), 3) AS fcr_rate
FROM flagged
GROUP BY ALL
ORDER BY week_start, contact_driver;
