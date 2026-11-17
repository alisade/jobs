-- "My open opportunities" for the pipeline view. $1 owner id.
SELECT id, name, stage, amount, close_date
FROM opportunities
WHERE owner_id = $1
  AND stage NOT IN ('closed_won', 'closed_lost')
ORDER BY close_date NULLS LAST, id
LIMIT 100
