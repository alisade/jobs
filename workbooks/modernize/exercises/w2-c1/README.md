# modernize/w2-c1 - Reverse-engineer claimdesk-web into an evidence-backed inventory and spec

**Type:** coding | **Estimate:** 2.5 hours | **Study plan:** Week 2 (Mon: discovery checklist; Tue: subagent fan-out; Wed: C4; Thu: spec-driven output)

## Scenario

Corvane Mutual is about to hand ClaimDesk to a modernization pod (JDK 21, JBoss EAP 8 /
Jakarta EE 10, LDAP to OIDC). Nobody on the pod has seen the code. Before anyone changes a line,
you, as the lead, must produce the current-state spec the pod will plan against: what the
application touches, who it trusts, and what it assumes about its runtime. The last spec someone
wrote (by asking a chatbot) listed three tables and missed the batch job entirely, so the
architecture board now requires every claim to cite a file and line.

`app/` is a trimmed copy of the repository plus the ops files from the hosts. It does not need
to compile.

## What you have

| Path | What it is |
|---|---|
| `app/claimdesk-web/` | the WAR source: servlets, filter, DAOs, clients, an EJB timer, descriptors, JPA mapping, JSP |
| `app/config/claimdesk.properties` | prod config (secrets redacted) |
| `app/ops/` | JBoss `standalone.conf` overrides, the jboss-cli build script, crontab, a shell script |
| `spec/inventory.schema.json` | the inventory format (read it: field meanings and allowed values) |
| `spec/inventory.json` | the inventory you fill in (starts empty) |
| `spec/SPEC.md` | the human spec template |

## Requirements

1. Fill `spec/inventory.json` (schema in `spec/inventory.schema.json`): database objects,
   integrations (live and dead), authorization checks, scheduled jobs, runtime assumptions.
2. Every item has evidence: `{"ref": "app/<path>:<line>", "quote": "<text copied from that line>"}`.
   A quote that is not on the cited line counts as a fabricated claim.
3. Trace endpoints to where they are actually defined (a JNDI name in code is not the endpoint).
4. Do not report dead code as live behaviour, and do not invent objects that are not in `app/`.
5. Write `spec/SPEC.md` (C4 context and containers, data, security flows, integrations, runtime,
   risks and blast radius, open questions) and `ANSWER.md`.

Using an agent is encouraged; it is the point of the week. Then verify what it tells you.

## Acceptance criteria (what the grader checks)

- The inventory validates against the schema and every evidence reference resolves.
- Hidden coverage checks: every database touchpoint (including ones outside the Java SQL
  strings), every live integration traced to its configuration, every authorization check
  whatever its mechanism, both scheduled jobs, and the runtime assumptions that a JDK 21 / EAP 8
  move will break.
- Precision: no invented objects; dead code marked dead.
- `SPEC.md` is usable by a pod: risks tied to evidence, open questions named (rubric).

## How to run

```bash
make setup      # builds modernize/.venv
make check      # which evidence refs do not resolve
make test       # visible checks
# then from workbooks/ in Claude Code: /grade modernize/w2-c1
make clean
```
