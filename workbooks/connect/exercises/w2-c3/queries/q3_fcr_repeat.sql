-- Q3 First-contact resolution proxy per local week and driver.
-- An answered contact is "repeated" when the same employee contacts again about the same driver
-- (any channel, answered or not) within 7 days (strictly after it started, at most 7 x 24 h later).
-- Output: week_start DATE, contact_driver VARCHAR, answered_contacts BIGINT, repeat_within_7d BIGINT,
--         fcr_rate DOUBLE = ROUND(1 - repeat_within_7d / answered_contacts, 3). Order: week_start, contact_driver.
-- TODO
SELECT NULL AS week_start, NULL AS contact_driver, 0 AS answered_contacts, 0 AS repeat_within_7d, 0.0 AS fcr_rate
WHERE FALSE;
