# fde/w3-c1 - AgentTrustMixin: per-hook fail policy over StorefrontBackend

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 3 (Wed: in-path checks + decision mapping, Thu: fail policy, logging)

## Scenario

Halyard Risk sells a real-time risk API (allow / deny / review per action). Northwind
Outfitters runs the commerce-agents retail vertical and wants Halyard in the agent's path
before launch: every cart write and every checkout gets a risk decision, with no change to
the prompt (the cache prefix must stay byte-identical) and no change to the blueprint repo.

You own the integration: `agent-trust-commerce`, a mixin that sits in front of any
`StorefrontBackend` in the MRO and maps Halyard's decisions onto the blueprint's **native**
results, so all three runtimes (Messages API, Agent SDK, Managed Agents via MCP) get the
same behavior through the shared executor.

The trust team signed off this matrix last week (your week-2 fail-policy matrix):

| Hook | allow | deny | review | timeout / risk error |
|---|---|---|---|---|
| `add_to_cart` | write | held, gate `trust` | write (settled at checkout) | **fail open** (150 ms budget) |
| `update_cart_item` (line grows) | write | held, gate `trust` | write | **fail open** |
| `update_cart_item` (line shrinks), `remove_from_cart`, all reads | not checked | | | |
| `checkout` (via `checkout_handoff`) | card renders | held, gate `trust` | held, gate `trust_review` | **fail closed** (400 ms budget) -> error result |

The fail mode and budget are per hook and come from `TrustPolicy` (`trust_mixin/policy.py`);
the table above is the default. A deployment may flip either hook.

## What you build

Edit `trust_mixin/mixin.py` (the TODOs). `decisions.py` and `policy.py` are given; do not
change them.

1. `AgentTrustMixin.__init__`: cooperative; the concrete backend's own constructor
   arguments still reach it (`TrustedRetail(data_dir=..., risk_client=...)`).
2. One private assessment path for every hook: builds a `RiskRequest` with **digests only**
   (`decisions.digest`), calls the client inside the hook's `asyncio.timeout` budget, and
   writes exactly one `DecisionRecord` per assessment to `decision_log`.
3. `add_to_cart`, `update_cart_item`, `checkout_handoff`: assess, then call `super()` or
   refuse, per the matrix.
4. `TrustAwareExecutor.domain_error`: maps your cart exceptions to `ToolOutcome`s.

## Acceptance criteria

- Allow is a pure passthrough: the result is exactly what the wrapped backend returns.
- Cart deny: `ToolOutcome.blocked == "trust"`, `is_error` false, text `CART_DENIED_TEXT`,
  nothing written. Checkout deny: held under `trust`, no `ui` event.
- Checkout review: held under `trust_review` with `CHECKOUT_REVIEW_TEXT`.
- The model never sees reason codes, decision ids, scores or the vendor name.
- A timeout, `RiskUnavailable`, or any other exception from the client follows the hook's
  `on_failure`; a fail-closed checkout is an **error** result (`CHECKOUT_UNAVAILABLE_TEXT`),
  a fail-closed cart write is an error result (`CART_UNAVAILABLE_TEXT`) with nothing written.
- The budget holds: a risk API that hangs for seconds costs a cart write ~150 ms.
- `update_cart_item` is assessed only when the line grows, and the request carries the delta.
- Reads, `remove_from_cart`, and `get_cart` (which the blueprint's gates call) never call
  the risk API. The blueprint's provenance gate still runs before any risk call.
- `RiskRequest` and `DecisionRecord` never contain the raw session id or user id.
- A log sink that raises does not change the decision.
- Task cancellation propagates as `CancelledError`; it is not logged or treated as fail-open.

## How to run

```bash
make setup     # builds/reuses the shared venv fde/.venv (blueprint installed editable)
make test      # visible tests (happy path + first denial)
# from workbooks/: /grade fde/w3-c1    (adds hidden tests for every criterion above)
make clean
```

Read first: `shopping-agent/core/shopping_agent/backend.py` (the contract),
`gates.py` (where cart writes are gated and the lock is held), `executor.py`
(`domain_error`), `commerce-common/commerce_common/presentation.py` (`PresentationRefused`)
and `enrichment.py` (`enrich_checkout` calls `checkout_handoff`).

## What to submit

Your `trust_mixin/mixin.py` and a filled-in `ANSWER.md`. Explain in particular why checkout
maps through `PresentationRefused` while cart writes map through `domain_error`, and what
happens to the cart lock while the risk call is in flight.
