# aiarch/w2-c1 - Help desk orchestrator with two Strands specialists

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 2 (Mon: agent loop and tools; Tue: multi-agent patterns; Wed: hooks)

## Scenario

The first Lighthouse agent at Harbor Point Mutual is an employee help desk. An orchestrator
routes each request to one of two specialists, exposed to it as tools (the Strands
"agents as tools" pattern): `it_requests` (tickets) and `access_reviews` (pending access
reviews per team). Security has two non-negotiable rules for the pilot, and both must hold
no matter what the prompt says: every tool call is audited, and no `delete_*` tool ever runs
without a human change. Finance wants a hard cap on model calls per request after a test
agent looped for 40 cycles overnight.

Everything runs offline. `helpdesk/testing.py` has `ScriptedModel`, a Strands model provider
that replays a script of tool calls and answers, so tests decide exactly what "the model"
does. `helpdesk/store.py` is a fake JSON store over `data/`. Both work as shipped.

## Requirements

1. **Tools** (`helpdesk/tools.py`). `get_ticket(ticket_id)` accepts only `IT-` plus five digits
   and returns only `id, summary, category, status`. `create_ticket(summary, category)`:
   summary 10-200 characters, category one of `hardware, software, network, access`; the
   requester is the signed-in user passed to `it_tools`, never a tool argument.
   `list_pending_reviews(team)`: team one of `payments, claims, underwriting, platform`;
   returns `{"team", "count", "reviews": [{"id", "user", "entitlement"}]}`. Invalid input
   or unknown ids raise `ToolInputError` with a message that says what was wrong and what
   is allowed (the model reads it and retries). Docstrings are the tool descriptions: write
   them for the model.
2. **Hooks** (`helpdesk/hooks.py`). `AuditHook(log)` appends
   `{"agent", "tool", "input", "status"}` per tool call with status `ok`, `error` or
   `blocked`, and cancels every `delete_*` tool with `BLOCK_MESSAGE`. `BudgetHook(n)` raises
   `BudgetExceeded` when one agent would make more than `n` model calls in a request.
3. **Agents** (`helpdesk/agents.py`). `build_orchestrator(model_factory, store, requester,
   audit_log, max_model_calls)` returns the orchestrator Agent (name `orchestrator`, tools
   `it_requests` and `access_reviews` only). Each tool runs a specialist Agent named like the
   tool, with its own model from `model_factory(name)`, its own system prompt, only its own
   tools, and both hooks, and returns the specialist's final text. A specialist that hits its
   budget comes back to the orchestrator as a tool error, not a crash.

## Acceptance criteria (what the grader checks)

- Routing, tool scoping per agent, trimmed outputs, validation messages, session requester.
- `delete_*` never runs and is audited as blocked; audit order across both levels.
- Budget: a looping specialist stops at the cap and the orchestrator sees an error; a looping
  orchestrator raises.
- `ANSWER.md`: why hooks and not prompt rules, and when you would move from agents-as-tools to
  a swarm, a graph or a workflow.

## How to run

```bash
make setup     # builds aiarch/.venv once (strands-agents, pytest)
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade aiarch/w2-c1
make clean
```

## What to submit

`helpdesk/tools.py`, `helpdesk/hooks.py`, `helpdesk/agents.py`, `ANSWER.md`.
