# fde/w4-c1 - Customer MCP server: trust-advisor tools for merchant engineers

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 4 (Wed: Customer MCP server), Week 2 (Mon: MCP servers), AI Integration (1: tool design, 4: security)

## Scenario

Merchants integrating `agent-trust-commerce` keep opening the same support tickets: "why
was this cart denied?", "is our policy file right?", "did we wire the mixin correctly?".
Halyard wants a **Customer MCP server** their merchant engineers connect to from Claude
Code: `trust-advisor`, a small set of read-only advisory tools over the decision export, the
policy format and the merchant's own backend classes.

The decision export is raw vendor data: session ids, customer emails, client IPs and
free-text analyst notes with phone and card numbers in them. A merchant engineer is not
allowed to see any of that. The server is the enforcement point: the model calling it will
happily repeat anything a tool returns.

## What you build

`trust_advisor/server.py` has `build_server()` and one finished tool, `list_reason_codes`,
as the pattern. Add four more and the helpers behind them:

| Tool | Helper | Returns (`trust_advisor/models.py`) |
|---|---|---|
| `explain_decision(decision_id)` | `redact.py: redact_text` | `DecisionExplanation` |
| `validate_policy_config(yaml_text)` | `policy_lint.py: lint_policy` | `PolicyReport` |
| `list_hooks_covered(backend)` | `hooks.py: hooks_covered` | `HooksReport` |
| `decision_stats(hook=None, last_n=200)` | (inline) | `DecisionStats` |

`models.py`, `store.py`, `reason_codes.py`, `sample_backends.py` and `data/` are given.

### Contracts

- **Every tool**: `readOnlyHint=True` (plus `destructiveHint=False`, `idempotentHint=True`,
  `openWorldHint=False`), a structured result (output schema), a description a model can
  act on, and bad input reported as an MCP **error result** (`ToolError`) with a useful,
  non-leaky message: never a traceback, never a raw record.
- **explain_decision**: ids look like `hx-1006-000123`; anything else (or longer than 32
  chars) is an error, as is an unknown id. Return `session_digest` (via `redact.digest`),
  never the session id, email or IP. Each reason code gets the catalog's meaning and action;
  a code not in the catalog gets the `UNKNOWN` wording, not an error. `analyst_note` is
  redacted: emails `[email]`, raw session ids `sess-...` `[session]`, IPv4 `[ip]`, card
  numbers (13-19 digits, spaces/dashes) `[card]`, phone numbers `[phone]`, capped at 500
  chars. Decision ids like `hx-1006-000117` inside a note are not PII and must survive.
- **validate_policy_config**: schema below. Input over 16,384 chars, invalid YAML, or a
  root that is not a mapping is an error result. Python tags must never execute
  (`safe_load`). Findings: `unknown_key` (error), `missing_section` (warning, for `cart` or
  `checkout`), `invalid_value` (error: `on_failure` not open/closed, `timeout_ms` not a
  number in (0, 5000], `failures` < 1 or not an int, `reset_s` <= 0), `yaml_boolean` (error:
  YAML 1.1 turned `on_failure: off` into `False`), `checkout_fail_open` (error),
  `budget_high` (warning: cart > 300 ms, checkout > 1500 ms). `valid` = no error finding.

  ```yaml
  cart:     {timeout_ms: 150, on_failure: open}
  checkout: {timeout_ms: 400, on_failure: closed}
  breaker:  {failures: 5, reset_s: 30}
  ```
- **list_hooks_covered**: `backend` is `package.module:ClassName`. Import it only when the
  module is in the server's `allowed_modules` (constructor argument; default
  `trust_advisor.sample_backends` and `retail.api`, matched on a module boundary). Bad
  format, a module outside the allowlist, an import failure, a non-class or a class that is
  not a `StorefrontBackend` are error results. Report, for each write hook (`add_to_cart`,
  `update_cart_item`, `remove_from_cart`, `checkout_handoff`), the first class in the MRO
  that defines it. The **concrete backend** is the first `StorefrontBackend` subclass in the
  MRO that defines a write hook itself; a **hook mixin** is a non-backend class that defines
  a write hook. A hook is `covered` when its defining class is a hook mixin in front of the
  concrete backend. `missing` lists required hooks (all but `remove_from_cart`) not covered;
  `misordered_mixins` lists hook mixins behind the concrete backend. `resolution_order` is
  the MRO as `module.QualName`, without `object`.
- **decision_stats**: `last_n` 1-1000, `hook` one of the three hooks or null, else error.
  Counts per outcome over the newest `last_n`, `fail_open_rate`, nearest-rank p95 latency;
  an empty window is zeros, not an error.

## Acceptance criteria

- Five tools, all read-only annotated with output schemas and real descriptions.
- No session id, email, IP, card or phone number from the export reaches any result.
- Every bad input is an `isError` result with a specific message; nothing crashes.
- YAML is parsed safely; a hostile tag is refused, not executed.
- `list_hooks_covered` is right for every class in `sample_backends.py` and refuses modules
  outside the allowlist.
- Stats match the raw records exactly.

## How to run

```bash
make setup
make test      # visible tests (one happy path per tool), in-memory MCP session
make serve     # optional: streamable HTTP on 127.0.0.1:8300/mcp; try it with MCP Inspector
# from workbooks/: /grade fde/w4-c1
make clean
```

Read first: the blueprint's `storefront_mcp_server.py` and its tests (in-memory client
session), `commerce_common/mcp_server.py` (`enforce_local_only_bind`), and the MCP spec on
tools (annotations, structured content, error results).

## What to submit

Your `trust_advisor/` changes and `ANSWER.md`. In ANSWER.md, say why `list_hooks_covered`
needs an allowlist even though it is "read-only", and how you would put auth in front of
this server for a multi-merchant deployment.
