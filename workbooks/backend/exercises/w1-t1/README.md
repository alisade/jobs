# backend/w1-t1 - Contacts attached to the wrong accounts after the pilot import

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 1 (Thu: CRM domain: Salesforce objects, IDs, hidden logic)

## Scenario

Keystone, Lumenfold's in-house replacement for its third-party CRM, ran its first pilot import last
week: a Salesforce-shaped CSV export of Accounts, Contacts, Opportunities and Tasks (`WhoId` points
at a Contact, the polymorphic `WhatId` at an Account or an Opportunity), plus a second Contact
extract from the legacy partner-portal app. The importer exited 0, but sales ops filed KEY-4471:
contacts sit under the wrong customer, about a dozen accounts are missing, and some tasks never
arrived. The reconciliation report shows a difference nobody could explain. The second pilot wave
(the partner portal) is blocked until you find the root cause and fix the importer.

## What you have

| Path | What it is |
|---|---|
| `incident/TICKET.md` | the ticket as sales ops wrote it |
| `incident/export/` | the export the pilot used (`Account.csv`, `Contact.csv`, `Opportunity.csv`, `Task.csv`, `partner_portal/Contact.csv`) |
| `incident/pilot/import.log`, `incident/pilot/recon.txt`, `incident/pilot/keystone.sqlite` | what the pilot run produced |
| `keystone_import/ids.py` | legacy id handling (`canonical_id` is the key every row is upserted on) |
| `keystone_import/importer.py` | the importer (SQLite stands in for the Keystone Postgres database) |
| `keystone_import/recon.py` | the reconciliation report: counts, checksums, orphans, rejects |
| `scripts/run_import.py` | runs importer + reconciliation into a folder |

## Your task

1. Find the root cause of the missing accounts and the misattached contacts. Prove it with
   evidence from the export, the pilot database and the code, not just a theory.
2. Fix it so that every legacy record keeps its own identity, the partner-portal extract links to
   the right accounts, re-running the import is idempotent, and the reconciliation report has zero
   unexplained mismatches while still listing the legitimately rejected rows with their reasons.
3. Decide whether the BOM warnings in the import log matter.
4. Write `ANSWER.md`: root cause with evidence, fix, how you verified it, and what you would add
   before the next migration wave.

Keep the public interface: `keystone_import.ids.canonical_id(raw) -> str` (the grader calls it),
`importer.import_export(export_dir, db_path)` and `recon.build_report(export_dir, db_path)`.
`canonical_id` should raise `ValueError` for anything that is not a Salesforce id.

## Acceptance criteria (what the grader checks)

- `canonical_id` gives the correct canonical id for 15- and 18-character input, keeps
  case-distinct ids distinct, and rejects malformed ids.
- Every account with a Name is imported exactly once; every contact (both extracts) points at the
  exact account its `AccountId` names.
- The reconciliation report is clean (`unexplained == 0`, counts and checksums match) and still
  lists the rejected rows; a second import run changes nothing.
- `ANSWER.md` explains the root cause with evidence (this carries most of the points).

## How to run

```bash
make setup     # generates incident/ (export, pilot run, ticket)
make import    # re-run importer + recon with your code into incident/run/
make test      # visible tests
sqlite3 incident/pilot/keystone.sqlite 'select count(*) from accounts'   # or python3 -c ...
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade backend/w1-t1
make clean
```
