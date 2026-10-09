# Reference: ms/w8-t1

## Root cause

`CreditCheckPlugin` is registered on **PreValidation (10)**, synchronous, Create of `contoso_order`, and it
**creates the `contoso_creditaudit` row there**. Learn's stage table: PreValidation "occurs before the main
system operation ... before the database transaction" for the initial operation; PreOperation and
PostOperation run "within the database transaction". The audit Create issued from stage 10 is therefore
its own operation and commits immediately. When `OrderValidationPlugin` (PreOperation 20) then throws for
an expired price list, the order's transaction rolls back, but the audit row is outside it and survives.
Declined orders leave a row too: the plug-in writes the audit, then throws.

Evidence: trace rows for CreditCheckPlugin show `Stage=10 Depth=1 InTransaction=False`; the ledger has
SO-58002 and SO-58005 (Approved) and SO-58003 (Declined) that are absent from `orders-export.csv`;
`sales-app.md` shows the price-list rejections for SO-58002/SO-58005 and the credit decline for SO-58003;
the gap 41280.00 - 29230.00 = 12050.00 = 8900.00 + 3150.00; `contoso_orderid` is empty on every ledger row
(the order id does not exist yet in PreValidation).

## Red herring

The `0x80044172` timeouts are ShippingQuotePlugin on 2026-09-12, fixed by INC-4471 (async PostOperation,
10 s timeout) on 2026-09-15; no rows since. A timeout fails the request and rolls back; it cannot create
an orphan.

## Fix (reference)

- Keep `CreditCheckPlugin` at PreValidation as a pure check: cheap cancellation before the transaction
  and before price-list validation, no writes. Put the available credit in `SharedVariables`.
- New `CreditAuditPlugin` on **PostOperation (40), synchronous**, Create of contoso_order: writes the
  ledger row inside the order's transaction, linked to `OutputParameters["id"]`. Reads the PreValidation
  shared variable from `ParentContext.SharedVariables` (Learn: for Create/Update/Delete, PreValidation
  shared variables are reached through ParentContext from later stages).
- Async PostOperation is a valid alternative (runs only after commit) but makes the ledger eventually
  consistent and needs idempotency on retries; synchronous 40 keeps the 1:1 invariant atomic.

## Remediation

Void ledger rows whose order number has no `contoso_order`: SO-58002, SO-58005 (approved exposure that
never existed) and SO-58003 (declined; the ledger is one row per created order). Going forward: a
reconciliation check (ledger rows without `contoso_orderid`), and a review rule: no data writes in
PreValidation steps.
