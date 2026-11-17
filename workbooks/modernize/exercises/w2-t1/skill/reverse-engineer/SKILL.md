---
name: reverse-engineer
description: Map an unfamiliar Java application before modernization. Use when asked to reverse engineer, inventory, or write a current-state spec for a repository. Produces spec/inventory.json and spec/SPEC.md with file:line evidence.
---

# Reverse-engineer a Java application

## Steps

1. List modules: `ls` the repository root and read every build file.
2. Database touchpoints: run `python3 scripts/scan_db.py <repo>` and record every table it reports
   in `db_objects`, with the file:line it gives.
3. Integrations: grep for HTTP clients, JMS, mail, LDAP, SFTP; trace each endpoint to config.
4. Authorization: web.xml constraints, `isUserInRole`, filters, JSPs, role tables.
5. Write the inventory and the spec. Every claim cites a file and line.

## Verification

- Every evidence reference must resolve (`make check` in the exercise repo).
- Ask a human to review the inventory before the pod plans from it.
