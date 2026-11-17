# Reference: backend/ai-c1 Tenant-scoped MCP tool server with an audit log

Reference files: `.grading/solution/keystone_mcp/server.py` and `identity.py`, model answer in
`.grading/solution/ANSWER.md`.

Core ideas:
- **Identity per session, not per argument.** The model controls arguments, so anything security
  relevant in an argument is attacker controlled (prompt injection through record content is expected).
- **Not found, not forbidden,** for other tenants' ids: no existence oracle.
- **One audit path.** A wrapper that owns the entry and maps typed outcomes makes "every call is
  audited" structurally true instead of a code-review promise.
- **Agents propose, workflows decide.** Risky writes become an approval workflow start with a
  deterministic id, so retries do not create duplicate approvals.
- **Idempotency keys scoped by tenant and user,** with a payload digest to reject key reuse.

## Interview angles
- "The services already enforce RLS. Why check tenancy in the tool server too?" (Defense in depth; the
  tool layer also controls existence leaks, error messages and audit outcomes; and not every downstream
  is a Postgres table.)
- "How would you rate-limit an agent that loops?" (Token bucket per agent session and per user at the
  gateway, budgets per conversation, a circuit breaker on repeated errors, alert on denial spikes.)
