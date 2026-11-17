-- Account timeline, newest first, keyset page of 50 (pipeline-svc, GET /v1/accounts/:id/timeline).
-- $1 tenant id, $2 account id, $3 occurred_at of the last row on the previous page, $4 its id.
-- kdb declares every string parameter as text (see scripts/db.js).
SELECT id, type, subject, occurred_at
FROM activities
WHERE tenant_id = $1
  AND account_id::text = $2
  AND (occurred_at, id) < ($3::timestamptz, $4::bigint)
ORDER BY occurred_at DESC, id DESC
LIMIT 50
