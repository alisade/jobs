# awsfde/w2-t1 - "Order tool unavailable" after the Gateway release

**Type:** troubleshooting | **Estimate:** 1.5 hours | **Study plan:** Week 2 (Tue: AgentCore Gateway; Thu: Identity; Fri: Observability)

## Symptom

Acme Foods is piloting Tidewater Ask with its tools behind an **AgentCore Gateway** Lambda target.
Release 2026.11.12 went out at 09:14 on Thursday. Since then the agent answers every purchase order
and invoice question with "I'm sorry, the order lookup tool is currently unavailable", while
searching orders still works. The platform team suspects the new Cognito JWT authorizer or the new
gateway execution role. Read `evidence/TICKET.txt` first.

## What you have

| Path | What it is |
|---|---|
| `evidence/TICKET.txt` | the customer ticket and the internal notes |
| `evidence/agent-transcript.txt` | the agent's view of one failing conversation |
| `evidence/gateway-auth-2026-11-12.log` | gateway control-plane and auth events around the deploy |
| `evidence/gateway-target.json`, `evidence/release-2026.11.12.diff` | the target definition and what shipped |
| `run/gateway-2026-11-12.log` | MCP requests and results for the pilot traffic (created by `make setup`) |
| `run/lambda-tw-order-tools-prod.log` | the function's log lines for the same traffic |
| `order_tools/` | this checkout: the Lambda (handler, tools, tool schema) |
| `replay/` | an emulation of the Gateway's MCP front end for a Lambda target: `tools/list` from the schema with the target prefix, `tools/call` invoking the function with the event and `client_context.custom` the Gateway docs describe. Treat it as the environment, not the suspect. |

## Your task

1. Find the root cause and prove it: which component fails, on which input, and why `search` works.
   Decide whether the authorizer and the execution role are involved, with evidence.
2. Fix `order_tools/handler.py`:
   - resolve the tool name from `bedrockAgentCoreToolName` (`<targetName>___<toolName>`) so it
     works for any target name, including names with single underscores or hyphens; a name without
     the prefix (direct invoke) is used as is;
   - a truly unknown tool, input that fails the tool's `inputSchema` (`tools.json`), and a missing
     order all come back as an error object `{"error": {"code", "message"}}` (codes `UNKNOWN_TOOL`,
     `INVALID_INPUT`, `NOT_FOUND`), never as an unhandled exception.
3. Verify with `make test` and `make replay` (one legitimate miss, PO-99999, should remain).
4. Write `ANSWER.md`: Approach, Root cause (with log lines and commands), Fix (and verification),
   Trade-offs / production follow-ups.

## Acceptance criteria (what the grader checks)

- Tool names split once on `___` for every target name shape; all three tools dispatch.
- Unknown tool, invalid input and not-found are error results with the right codes.
- The replay shows no function errors except the PO-99999 miss; tool behavior unchanged.
- `ANSWER.md` names the mechanism with evidence and rules the auth change in or out.

## How to run

```bash
make setup     # shared venv + replays the pilot traffic into run/
make test
make replay    # after a fix
# from workbooks/: /grade awsfde/w2-t1
make clean
```
