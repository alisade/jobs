# aiarch/ai-c1 - A change-management MCP server for Lighthouse

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** AI Integration (tool design, security, Build 2) and Week 4 (MCP servers)

## Scenario

Harbor Point's agents need to file and follow change tickets. The change system has a REST
API and the service catalog lives in a CMDB. A one-tool-per-endpoint wrapper was tried in the
pilot and failed the way such wrappers do: the model picked the wrong endpoint, passed
free-text service names the change API rejected, pulled 400-line ticket histories into its
context, and once filed a change "on behalf of" a user named in a ticket comment. You are
building the replacement: a small MCP server with four task-shaped tools, which will run on
AgentCore Runtime and sit behind the gateway as an MCP server target.

`changemgmt/backends.py` has the fake change store, the fake CMDB and a stand-in token
verifier; `data/` holds their records. They work as shipped. Tests use the official MCP
Python SDK (2.x: `MCPServer`, `ToolError`, an in-process `Client`).

## Requirements (`changemgmt/server.py`)

`build_server(store, cmdb, caller_token, verifier)` verifies the token first (an invalid
token raises and no server is built) and returns an `MCPServer` named `change-management`
whose tools act as that caller. No tool has a `requester`, `user`, `author` or similar
argument.

1. `create_change(service, summary, risk, window_start)`: service must exist in the CMDB and
   be `active` (unknown names get an error with the closest matches); summary 10-200
   characters; risk `low`, `medium` or `high`; window_start an ISO 8601 time with timezone,
   in the future, at most 90 days ahead, and at least 48 hours ahead for high risk. Returns
   only `change_id`, `state` and `approver_group` (the service's owner group).
2. `get_change(change_id)`: id `CHG-` plus five digits, rejected before the backend is called
   when malformed; returns the summary fields plus `requester` and `comment_count`, never the
   comment bodies; not found tells the model to use `list_my_open_changes`.
3. `list_my_open_changes(cursor?)`: the caller's changes in draft, submitted or scheduled,
   five per page, with an opaque `next_cursor` (null on the last page); a bad cursor is an
   actionable error.
4. `add_comment(change_id, text)`: text 1-2000 characters; only the requester or a member of
   the service's owner group may comment, and the error says who may.
5. Read tools carry the read-only annotation; write tools do not. Every tool description is
   written for the model (what it does, valid inputs).
6. Validation errors and business errors come back as tool errors (`is_error`), so the model
   can read them and retry.

## Acceptance criteria (what the grader checks)

- Tool list, schemas without identity arguments, annotations, descriptions.
- Validation and business rules on every tool, small outputs, pagination, comment permissions,
  invalid tokens.
- `ANSWER.md`: five rules for MCP tool design from the servers you use every day and where
  each shows up here, and how this server would be deployed (Runtime with the MCP protocol,
  gateway target, JWT audience validation, no token passthrough).

## How to run

```bash
make setup     # builds aiarch/.venv once (mcp, pydantic)
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade aiarch/ai-c1
make clean
```

## What to submit

`changemgmt/server.py` and `ANSWER.md`.
