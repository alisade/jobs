SELECT id, type, subject, occurred_at
FROM activities
WHERE tenant_id = $1
  AND account_id = $2
  AND (occurred_at, id) < ($3::timestamptz, $4::bigint)
ORDER BY occurred_at DESC, id DESC
LIMIT 50
