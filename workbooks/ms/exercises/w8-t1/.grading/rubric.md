# Rubric: ms/w8-t1 Credit ledger has rows for orders that were never created
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause | 30 | Full: CreditCheckPlugin is registered PreValidation (10); for the initial operation that stage runs before/outside the database transaction, so the ledger row it creates is committed on its own. When OrderValidationPlugin (PreOperation 20, inside the transaction) rejects the order, only the transaction rolls back; the ledger row stays. Also explains the declined rows (written then the plug-in throws). Partial: "wrong stage" without the transaction mechanism. Zero: timeouts, duplicates, or Finance's report. |
| 3 | Evidence | 15 | Quotes InTransaction=False / Stage=10 trace lines, SO-58002 and SO-58005 in the ledger but not in orders with the price-list error in sales-app.md, the 12050.00 gap (41280.00 vs 29230.00), the declined SO-58003 row, empty contoso_orderid, the step export. |
| 4 | Red herring | 5 | Dismisses the 0x80044172 Sandbox Host timeouts: ShippingQuotePlugin, 2026-09-12, fixed in INC-4471 (now async), no rows since, and a timeout would roll back rather than leave a row. |
| 5 | Fix quality | 10 | Full: validation stays at 10 with no writes, ledger written by a PostOperation (40) step in the transaction with the order id, decision passed via ParentContext.SharedVariables (or recomputed) and justified; async 40 acceptable if justified with its trade-off (eventual, needs idempotency). Partial: everything moved to 20/40 losing the cheap cancel, or no order link. |
| 6 | Remediation and production | 10 | Lists rows to void (SO-58002, SO-58005, and the declined SO-58003 per the one-row-per-order rule), a cleanup approach (query ledger rows with no matching order), and guard rails (code review rule "no writes in PreValidation", reconciliation alert). |
Total: 100
