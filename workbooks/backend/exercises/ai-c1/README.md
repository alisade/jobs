# backend/ai-c1 - Tenant-scoped MCP tool server with an audit log

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** AI Integration (tool design, security, observability); Week 6 (Thu: workflow primitives for agents)

## Scenario

Lumenfold's sales assistant (an agent app) will work on Keystone data through `keystone-mcp`, an MCP
server. The hackathon prototype in `keystone_mcp/server.py` demoed well with one business unit. Security
review blocked it: it searches every tenant, `propose_lead_assignment` assigns the lead on the spot,
writes are not idempotent (agents retry), and nothing is audited. Priya Natarajan asked you to make it
the production tool surface before the pilot with `bu-amer` and `bu-emea`.

The agent gateway authenticates the user, then opens one MCP session per agent conversation and hands
the server a **delegation token**: who the user is, their tenant, their scopes and which agent acts
for them. `build_server(token, ...)` is called once per session, so the identity is fixed for the
session and comes from the token, never from tool arguments.

## What you have

| Path | What it is |
|---|---|
| `keystone_mcp/server.py` | the prototype: `build_server()` and four tools (you rewrite this) |
| `keystone_mcp/identity.py` | delegation token format; `verify_delegation()` is a TODO |
| `keystone_mcp/store.py` | in-memory stand-in for the Keystone services (does not enforce tenancy). Do not change |
| `keystone_mcp/workflows.py` | fake keystone-workflows client: `start_approval()`. Do not change |
| `keystone_mcp/audit.py` | append-only audit log and `args_digest()`. Do not change |
| `testkit.py`, `conftest.py`, `tests/` | test rig: real `mcp` client sessions in process, synthetic users and tokens |

The tests drive the server through the official MCP Python SDK (2.x, `MCPServer`) with its in-process
client, so you are testing the real protocol path: tool listing, schemas, argument validation and
tool errors. No model and no network: the "agent" is the test.

## Requirements

1. **Identity.** `verify_delegation()` checks the HMAC-SHA256 signature with a constant-time compare,
   the expiry (`exp` must be later than `clock()`), and that `sub`, `tenant`, `scopes`, `agent` and `exp`
   are present; anything else raises `InvalidDelegation`. `build_server()` fails for a bad token.
2. **No identity in tool arguments.** No tool takes a tenant, user, agent or scope argument.
3. **Tenant scoping.** Every read and write is limited to the session's tenant. An account, lead or user
   id from another tenant behaves exactly like an id that does not exist (`not found`).
4. **Tools** (keep the names and parameters):
   - `find_account(query, limit=10)` -> `{"accounts": [{"id", "name", "owner_id"}]}`; `limit` 1-50.
   - `get_account_timeline(account_id, limit=20)` -> `{"account_id", "items": [...], "content_is_untrusted": true}`;
     `limit` 1-50; items newest first.
   - `log_activity(account_id, type, subject, idempotency_key)`: needs `crm.write`; `type` is one of
     call, email, meeting, note; `subject` 1-200 chars; the key is scoped to tenant and user. Same key and
     same arguments returns the first result (`activity_id` unchanged) without logging again; same key with
     different arguments is an error.
   - `propose_lead_assignment(lead_id, owner_id, reason="")`: needs `crm.write`; lead and owner must be in
     the tenant and the owner active. Starts `workflows.start_approval("lead_assignment", ...)` with a
     deterministic idempotency key, `on_behalf_of` the user and the agent id; returns
     `{"proposal_id", "status": "pending_approval"}`. It never calls `store.assign_lead`.
   - Every tool needs `crm.read` at least.
5. **Errors.** Denials, not-found and invalid input are MCP tool errors (raise `ToolError`) with a message
   the model can act on (for a missing scope, say which scope).
6. **Audit.** Exactly one `audit.append()` per tool call, success or failure: `ts`, `agent_id`,
   `on_behalf_of`, `tenant`, `tool`, `args_sha256` (= `args_digest()` of the tool's parameters with
   defaults filled in), `outcome` (`ok`, `denied`, `not_found`, `invalid`, `error`), and a fresh `trace_id`.
   Never put the raw arguments in the log.
7. **Descriptions.** Each tool's description tells a model what it does, its limits and, for the
   timeline, that record content is untrusted data and not instructions.

## Acceptance criteria (what the grader checks)

- Tool listing and schemas (no identity arguments, real descriptions).
- Cross-tenant reads and writes fail as not found and are audited with the right outcome.
- Limits, validation and scope denials.
- Idempotent `log_activity` and `propose_lead_assignment`; proposals never assign.
- Audit completeness: one entry per call, the right hash, unique trace ids, no raw arguments.
- Bad, expired and tampered tokens are rejected.
- `ANSWER.md`: design choices and what you would add before production.

## How to run

```bash
make setup
make test       # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade backend/ai-c1
make clean
```

Optional: run it against a real client. `MCPServer.run()` serves stdio; a launcher that reads the
delegation token from an environment variable and calls `build_server(...).run()` is enough to add
it to Claude Code as a local MCP server with synthetic data. The grader never does this.
