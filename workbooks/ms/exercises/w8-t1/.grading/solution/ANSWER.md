# ms/w8-t1 answer

## Approach
Compared creditaudit-export.csv with orders-export.csv, matched the extra order numbers to sales-app.md,
then read the trace rows and the step export, then the plug-in source.

## Root cause
CreditCheckPlugin runs at PreValidation (stage 10) and creates the contoso_creditaudit row there. For the
initial operation, PreValidation runs outside the database transaction (trace: "Stage=10 Depth=1
InTransaction=False"), so the audit Create commits on its own. OrderValidationPlugin runs at PreOperation
(20) inside the transaction; when it rejects SO-58002 and SO-58005 ("Price list FAB-2026Q3 expired"),
the order rolls back but the ledger rows stay. SO-58003 also has a Declined row because the plug-in writes
before throwing. Ledger approved total 41280.00 vs orders 29230.00: gap 12050.00 = 8900.00 + 3150.00.
contoso_orderid is empty on all rows because the order id does not exist in PreValidation.

The 0x80044172 Sandbox Host timeouts are ShippingQuotePlugin on 2026-09-12, fixed by INC-4471 (now async);
a timeout rolls back, it cannot leave a row. Unrelated.

## Fix
- CreditCheckPlugin stays at stage 10 as a pure check (cheap cancel, no writes) and passes the available
  credit in SharedVariables.
- New CreditAuditPlugin, PostOperation (40), synchronous, Create of contoso_order: writes the ledger row in
  the same transaction, linked to OutputParameters["id"], reading the value from ParentContext.SharedVariables.
- Verified: make test green; make setup shows 4 ledger rows for 4 orders and equal totals.

## Trade-offs / what I would do in production
- Void SO-58002, SO-58005 and SO-58003 ledger rows (no matching order); script: ledger rows with no order.
- Sync PostOperation keeps the ledger atomic with the order at the cost of a bit of save latency; async would
  be eventually consistent and need idempotency.
- Review rule: no writes in PreValidation; daily reconciliation alert on ledger rows without an order link.
