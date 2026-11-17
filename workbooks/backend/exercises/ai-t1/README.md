# backend/ai-t1 - The assistant showed another business unit's pipeline

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** AI Integration (4 Security, 1 Tool design); Week 1 (Fri: LLM security)

## Scenario

Keystone exposes CRM data to Lumenfold's sales assistant through `keystone-mcp`. The MCP server
verifies the user's delegation token when the session opens and builds a `Session` (agent, user,
tenant, scopes, trace id). On 2026-11-12 Jordan Lee, an AMER account executive, asked the assistant
about Brightwater Logistics and the answer included an EMEA deal: amount, competitor bid and a legal
redline. Security opened INC-7731 as an S1 data exposure. The assistant team has already drafted a
fix (`incident/proposed-fix.md`). You own the tool layer.

## What you have

| Path | What it is |
|---|---|
| `incident/TICKET.md` | the report (created by `make setup`) |
| `incident/keystone-mcp.log` | server log for the session, including tool arguments |
| `incident/audit-excerpt.log` | the audit rows for the session |
| `incident/proposed-fix.md`, `incident/assistant-config.yaml` | the assistant team's proposal and config |
| `transcripts/inc-7731.json` | the recorded session: the model's tool calls and its final reply |
| `assistant_tools/` | `tools.py` (schemas and handlers), `session.py`, `audit.py`, `data.py`, `replay.py` |

`make replay` re-issues the recorded model turns against the current tool code, offline: there is no
model and no API key; the "model" is the recording.

## Your task

1. Find the root cause and back it with evidence. Distinguish what triggered the leak from what
   allowed it, and say what you think of each item in the proposed fix.
2. Fix `assistant_tools/tools.py` (keep `call_tool(session, name, args)`, `TOOLS` and the result shape
   `{"is_error": bool, "content": ...}`):
   - tenant and user come only from the `Session`; no tool schema has a tenant argument; schemas are
     closed (`additionalProperties: false`) and unknown arguments are rejected (audited as `denied`);
   - an account id from another tenant gets the same "account not found" as a missing one;
   - `limit` is an integer from 1 to 50 (default 20);
   - every timeline item carries `"untrusted": true`, and the tool description tells the model notes are data;
   - every call, including errors and denials, writes one audit entry with `ts`, `trace_id`,
     `agent_id`, `on_behalf_of`, `tenant_id`, `tool`, `args_sha256` (use `audit.args_sha256`) and
     `outcome` (`ok`, `denied`, `not_found` or `error`).
3. Fill in `ANSWER.md`, including what you would tell security.

## Acceptance criteria (what the grader checks)

- Replaying the transcript yields no other-tenant data and the injected call returns an error.
- Schemas: no tenant property, closed; tenant arguments rejected and audited.
- Cross-tenant ids are not found; the owning tenant still reads its account normally.
- Complete audit entries for every call; untrusted marking; limit bounds.
- `ANSWER.md` root cause and evidence carry most of the points.

## How to run

```bash
make setup      # venv + incident bundle
make replay     # what the recorded model turns get from your tools
make test       # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade backend/ai-t1
make clean
```
