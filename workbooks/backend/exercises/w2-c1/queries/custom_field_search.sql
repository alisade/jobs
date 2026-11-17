-- Search accounts by a custom field (Salesforce __c fields land in custom_fields). $1 jsonb filter.
SELECT id, name
FROM accounts
WHERE custom_fields @> $1::jsonb
LIMIT 50
