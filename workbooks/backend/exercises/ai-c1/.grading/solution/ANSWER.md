# ANSWER: backend/ai-c1 Tenant-scoped MCP tool server with an audit log

## Approach

One server instance per agent session: `build_server()` verifies the delegation token first, so a
bad or expired token never produces a server, and every tool closes over the verified `Identity`. A
small `run(tool, args, fn)` wrapper builds the audit entry (identity, args hash, fresh trace id) and
appends it exactly once with the outcome mapped from typed exceptions, so no tool can forget to audit
or audit twice. Tenancy checks live in two helpers (`own_account`, lead/owner checks) that treat
another tenant's id exactly like a missing one, so the agent cannot even probe which ids exist.

## Fix

- `verify_delegation`: HMAC recomputed and compared with `hmac.compare_digest`, all claims required,
  `exp` checked against the injected clock.
- `find_account` searches only the session tenant; `get_account_timeline` checks the account's tenant,
  bounds `limit`, and marks content untrusted (also stated in the tool description and the server
  instructions, but the scoping is the control, not the wording).
- `log_activity` requires `crm.write`, validates type, subject and key, stores
  `(tenant, user, key) -> (args digest, result)`: replays return the first result, a different payload
  is an error.
- `propose_lead_assignment` checks lead and owner tenancy and the owner's status, then starts the
  approval with key `tenant:lead-assign:lead:owner`, so retries return the same proposal. It never
  touches `assign_lead`; the workflow does that after a manager approves.
- Audit: one entry per call with `args_digest` over the parameters (defaults included), never the raw
  arguments. Verified with `make test` and the full hidden-style session tests (two tenants, denials).

## Trade-offs / what I would do in production

Replace the HMAC token with OAuth token exchange (RFC 8693) and audience-bound short-lived tokens, and
pass the user identity on to the services so Postgres RLS applies as a second wall. Keep idempotency
state in the service (not in the MCP process memory) so it survives restarts and scales out. Add
per-agent and per-user quotas at the gateway, a kill switch per agent app, ship the audit log to an
append-only store with a query UI for security, and run evals on tool usage (did it propose instead of
assign, did it stay in the tenant, did it follow instructions from record content).
