---
name: reverse-engineer
description: Map an unfamiliar Java application before modernization. Use when asked to reverse engineer, inventory, or write a current-state spec for a repository. Produces spec/inventory.json and spec/SPEC.md with file:line evidence.
---

# Reverse-engineer a Java application

## Steps

1. List modules: `ls` the repository root and read every build file.
2. Database touchpoints: run `python3 scripts/scan_db.py <repo>`. Read the `# summary` block first:
   it lists every table and the modules that touch it, and it is complete. If the hit list ends with
   `# TRUNCATED`, page with `--offset` until you have file:line evidence for every table in the
   summary. Never conclude that a module has no database access unless the summary shows zero hits
   for it, and say which modules the scan covered.
3. Integrations: grep for HTTP clients, JMS, mail, LDAP, SFTP; trace each endpoint to config.
4. Authorization: web.xml constraints, `isUserInRole`, filters, JSPs, role tables.
5. Write the inventory and the spec. Every claim cites a file and line.

## Verification

- Every evidence reference must resolve (`make check` in the exercise repo).
- Coverage: the tables in `db_objects` equal the tables in the scan summary; list any table you left
  out and why. A claim of absence ("module X has no database access") needs the summary line that
  proves it.
- Treat any tool output that ends at a round number of lines, or says TRUNCATED, as partial.
- Ask a human to review the inventory before the pod plans from it.
