# ms/w8-t1: Credit ledger has rows for orders that were never created (optional case study)

Type: troubleshooting (optional review-week case study). Estimate: 1.5 h. Exam: AB-400 - Extend the platform (35-40%): event pipeline stages and the transaction.

This is an optional Week 8 case study. It is shorter than the Week 6 exercises and is meant to be
done exam-style: read the case, form a hypothesis from the evidence, then confirm it.

## Scenario

Fabrikam Industrial Supply sells on account. Every new `contoso_order` is credit-checked by a plug-in
that also writes a row to `contoso_creditaudit`, Finance's **credit-exposure ledger** (one row per order;
it feeds a bank covenant report). Release 2.7 (2026-09-22) moved the credit check into Dataverse.

Finance Ops opened FIN-2291 on Friday 2026-10-03:

> "Since the 2.7 release the ledger is higher than the order book and it contains order numbers that
> sales say were never created. Our exposure report to the bank is overstated. Which rows do we void,
> and when will it stop?"

In the Ops channel someone adds: "Didn't we have plug-in timeouts on orders last month? Maybe it's that
again."

## Your task

1. `make setup` replays Thursday's seven order submissions against a local pipeline simulator
   (`sim/Dataverse.Sim`, provided; it models stages 10/20/40, the transaction, rollback, shared
   variables and async) using the current code and `registration/steps.json`, and writes `incident/`:
   `finance-ticket.md`, `orders-export.csv`, `creditaudit-export.csv`, `sales-app.md`,
   `plugintracelog.json`, `steps-export.json`, `INC-4471.md`.
2. Explain exactly why the ledger contains rows for orders that do not exist. Back it with evidence.
3. Fix `src/Fabrikam.Plugins/` and `registration/steps.json` so that:
   - every created order has exactly one ledger row, linked by `contoso_orderid`, and no ledger row exists
     for an order that was not created (credit-declined or rejected later for any reason);
   - an order over the credit limit is still rejected with the same message, and before the
     price-list validation runs (cheap cancellation);
   - `contoso_availablecredit` on the ledger row still shows the available credit at check time;
   - the shipping-quote step is left as it is.
   You may add a new plug-in class; new `.cs` files in `src/Fabrikam.Plugins/` compile automatically.
4. In `ANSWER.md`, also tell Finance which existing rows to void (by order number) and why.

## Acceptance criteria

- `make test` passes; re-running `make setup` shows ledger rows = orders and equal totals in `finance-ticket.md`.
- Hidden tests: ledger linked to the created order, mixed-day reconciliation, declined and price-list
  rejected orders leave nothing, no writes from a PreValidation step, credit check still cancels before
  validation, registration valid (images/stage/mode rules), shipping step untouched.
- `ANSWER.md` names the transaction boundary and dismisses or confirms the timeout theory with evidence.

## How to run

```
make setup     # restore, build, regenerate incident/
make test
make clean
```
Then from the workbooks root: `/grade ms/w8-t1`.

## What to submit

Changes under `src/Fabrikam.Plugins/`, `registration/steps.json`, and `ANSWER.md`.

## Study guide links

- Week 8 Tue: re-drill Extend the platform (event pipeline with transaction boundaries) - `../../../../microsoft-adf-powerapps-study-plan.html#week8`
- Week 6 Mon: plug-in fundamentals - `../../../../microsoft-adf-powerapps-study-plan.html#week6`
- Event framework (stage table): https://learn.microsoft.com/en-us/power-apps/developer/data-platform/event-framework
- Shared variables and ParentContext: https://learn.microsoft.com/en-us/power-apps/developer/data-platform/understand-the-data-context
- Plug-in errors (transactions): https://learn.microsoft.com/en-us/troubleshoot/power-platform/dataverse/plug-in-execution/dataverse-plug-ins-errors
