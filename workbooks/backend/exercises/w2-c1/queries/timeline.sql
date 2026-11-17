-- Account timeline, newest first, keyset page of 50.
-- $1 account id, $2 occurred_at of the last row on the previous page, $3 id of that row.
-- The tenant comes from RLS (app.tenant_id), not from a WHERE clause.
SELECT id, type, subject, occurred_at
FROM activities
WHERE account_id = $1::bigint
  AND (occurred_at, id) < ($2::timestamptz, $3::bigint)
ORDER BY occurred_at DESC, id DESC
LIMIT 50
