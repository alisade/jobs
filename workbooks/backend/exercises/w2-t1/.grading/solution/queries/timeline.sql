-- Account timeline, newest first, keyset page of 50 (pipeline-svc, GET /v1/accounts/:id/timeline).
-- $1 tenant id, $2 account id, $3 occurred_at of the last row on the previous page, $4 its id.
-- kdb declares every string parameter as text: cast the PARAMETER to the column type, never the
-- column to the parameter type, so the predicate stays an index condition.
SELECT id, type, subject, occurred_at
FROM activities
WHERE tenant_id = $1
  AND account_id = $2::uuid
  AND (occurred_at, id) < ($3::timestamptz, $4::bigint)
ORDER BY occurred_at DESC, id DESC
LIMIT 50
