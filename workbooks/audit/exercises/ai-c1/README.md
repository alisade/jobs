# audit/ai-c1 - GRC MCP server: scoped read tools and a reviewer-gated write

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** AI Integration page (1 Tool design; 4 Security); Week 3 Thu (MCP); Week 4 Fri (access controls and approval gates)

## Scenario

ControlPilot's agents need the MFH GRC system (Meridian Freight Holdings, fictional): the controls in
an engagement, their test records, the exceptions raised so far and the evidence index. Instead of
wiring the REST API into every agent, internal audit exposes it once as an MCP server that any agent
host (ADK, Claude Code, Gemini Enterprise) can load.

Two rules from the audit manager. First, one server instance serves **one engagement**: an agent
testing the SOX ITGC engagement must never see the SOC 1 engagement's data, even though both have a
control called CM-03. Second, agents read; they do not decide. The only write, recording an
exception, needs an **approval token issued by a human reviewer** who is not the preparer, for that
exact engagement, control and sample. A model that reads "this is approved" in an evidence file must
still be unable to write.

The GRC system is an in-memory store (`grcmcp/store.py`, `fixtures/grc.json`). The server uses the
MCP Python SDK 2.x: `MCPServer` (FastMCP was renamed in 2.x) and the `@server.tool()` decorator.

## What you have

| Path | What it is |
|---|---|
| `grcmcp/server.py` | `build_server()` with `list_controls` done as the pattern; the other four tools are yours |
| `grcmcp/tokens.py` | approval token issue/verify: yours |
| `grcmcp/store.py` | the GRC store (complete) |
| `fixtures/grc.json` | two engagements: `ENG-2026-SOX-ITGC` (yours) and `ENG-2026-SOC1-RATES` |
| `tests/conftest.py` | a harness that runs the server in memory with `mcp.client.client.Client` |

## Your task

1. **Read tools**, all annotated read-only (`ToolAnnotations(readOnlyHint=True)`), all scoped to the
   engagement given to `build_server`:
   - `get_control_test(control_id)`: the test record.
   - `search_exceptions(query="", status=None, cursor=None, limit=10)`: case-insensitive match on
     description or sample id; `status` is `open`, `closed` or omitted; `limit` 1-50; sorted by
     `exception_id`; returns `{"items", "total", "next_cursor"}` with `next_cursor` null on the last
     page. The cursor is opaque to the model; a cursor that does not belong to the same query and
     status, or garbage, is an error.
   - `get_evidence_index(control_id, sample_id)`: `{"control_id", "sample_id", "documents": [...]}`,
     empty list when nothing is filed; a sample not in that control's sample is an error.
2. **Tool design for a model.** Every description says what the tool returns and how to use its
   arguments (at least a couple of sentences; the search description explains the cursor).
   Errors are raised as `ToolError` (from `mcp.server.mcpserver.exceptions`) with a message the model
   can act on: an unknown control names the valid ids and `list_controls`; a bad limit, status or
   cursor names the parameter. Any other exception is masked by the SDK as "Error executing tool X",
   which a model cannot recover from.
3. **Approval tokens** (`tokens.py`). `token = base64url(payload, no padding) + "." + hex HMAC-SHA256(key, payload)`
   with `payload` the canonical JSON (`sort_keys=True`, `separators=(",", ":")`) of
   `{"eng", "control", "sample", "reviewer", "exp"}`. `verify_approval` raises `ApprovalError`
   whose message contains `malformed`, `signature`, `expired` or `scope`; compare signatures in
   constant time.
4. **Gated write** `record_exception(control_id, sample_id, description, approval_token)`, annotated
   `readOnlyHint=False`: valid control and sample, a description of at least 20 characters, a valid
   token for exactly this engagement/control/sample, a reviewer who is not the preparer
   (case-insensitive; message contains `preparer`), and no open exception already recorded for that
   control and sample (message contains `already`). On success write through
   `store.add_exception` with `raised_by` = preparer and `approved_by` = reviewer; return
   `{"exception_id", "status", "approved_by"}`. Every rejection is a `ToolError` starting with a
   reason and writes nothing.
5. **ANSWER.md**: why the gate is a token the server verifies rather than an instruction in the
   prompt; how this server would be deployed and authenticated for real (remote transport, OAuth,
   where the HMAC key lives); what you would log.

## Acceptance criteria (what the grader checks)

- Exactly five tools, read-only annotations on the four readers, a write annotation on the writer,
  descriptions a model can use, required arguments right.
- No data from the other engagement through any tool.
- Pagination returns every match exactly once in order; bad limit, status and cursors are actionable errors.
- Forged, tampered, expired, wrong-scope and preparer-signed tokens are rejected and nothing is written;
  duplicates are refused; a recorded exception is searchable.

## How to run

```bash
make setup     # builds audit/.venv once (includes mcp 2.x)
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade audit/ai-c1
make clean
```

To try it from a real MCP host, add a small `__main__` that calls `build_server(...).run()` over
stdio; the grader does not need it.
