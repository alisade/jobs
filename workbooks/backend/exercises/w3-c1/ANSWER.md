# ANSWER: backend/w3-c1 Idempotency keys that survive concurrent retries

## Approach

<!-- Why the original version races, and the protocol you chose (claim, run, complete or release). -->

## Fix

<!-- What you changed and how you verified it (which tests, how you reproduced the race). -->

## Trade-offs / what I would do in production

<!-- Short: Postgres specifics (INSERT ... ON CONFLICT DO NOTHING RETURNING, one transaction vs two),
crash between the handler and the completion write (stuck in_progress rows, a lease), retention and
cleanup, what you store (status, headers, body size), keys from agents and workflow activities. -->
