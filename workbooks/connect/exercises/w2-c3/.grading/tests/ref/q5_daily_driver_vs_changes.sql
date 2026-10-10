-- Daily weekday password-reset volume and repeat rate, joined to the change calendar.
WITH pr AS (
  SELECT c.*, CAST(timezone('America/New_York', c.initiation_timestamp) AS DATE) AS local_date
  FROM contact_records c
  WHERE contact_driver = 'password_reset'
),
rep AS (
  SELECT local_date,
         COUNT(*) AS contacts,
         COUNT(*) FILTER (WHERE connected_to_agent_timestamp IS NOT NULL AND EXISTS (
           SELECT 1 FROM contact_records n WHERE n.employee_id = pr.employee_id AND n.contact_driver = pr.contact_driver
             AND n.initiation_timestamp > pr.initiation_timestamp AND n.initiation_timestamp <= pr.initiation_timestamp + INTERVAL 7 DAY)) AS repeated,
         COUNT(*) FILTER (WHERE connected_to_agent_timestamp IS NOT NULL) AS answered
  FROM pr
  GROUP BY local_date
)
SELECT r.local_date, r.contacts, ROUND(r.repeated / NULLIF(r.answered, 0), 3) AS repeat_rate,
       string_agg(c.change_id, ',' ORDER BY c.change_id) AS changes_that_day
FROM rep r
LEFT JOIN change_log c ON CAST(c.implemented_local AS DATE) = r.local_date
WHERE dayofweek(r.local_date) BETWEEN 1 AND 5
GROUP BY r.local_date, r.contacts, r.repeated, r.answered
ORDER BY r.local_date;
