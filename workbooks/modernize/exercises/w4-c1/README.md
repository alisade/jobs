# modernize/w4-c1 - javax.servlet to jakarta.servlet with characterization tests that stay green

**Type:** coding | **Estimate:** 2.5 hours | **Study plan:** Week 4 (Mon: characterization tests; Tue: javax to jakarta; Wed: app server targets)

## Scenario

`claimdesk-notes` is the small service the agent portal calls to read claims and add notes. It
runs on the Servlet 4.0 API (`javax.servlet`), embedded Tomcat 9. ClaimDesk is moving to JBoss
EAP 8 (Jakarta EE 10, Servlet 6.0), so this service moves to the `jakarta.servlet` namespace;
the team uses embedded Tomcat 10.1 (also Servlet 6.0) to prove it before the app server move.

The portal team parses this service's responses, including the error JSON. The pod recorded
golden masters of eight HTTP flows from production v3.7 into `src/test/resources/golden/`, and
`CharacterizationTest` replays them. It is green today. Your job is to keep it green.

A developer on the pod tried `sed -i 's/javax\./jakarta./g'` on a branch last week. It did not
compile, and once it did, two of the portal's error screens broke. Do better.

## What you have

| Path | What it is |
|---|---|
| `pom.xml` | `tomcat-embed-core` 9.0.x (javax) |
| `src/main/java/.../ClaimServlet.java` | the API |
| `src/main/java/.../ErrorServlet.java` | the error JSON the portal parses |
| `src/main/java/.../RequestIdFilter.java` | request id propagation |
| `src/main/java/.../JdbcSupport.java` | production datasource lookup (JNDI) |
| `src/main/java/.../NotesServer.java` | embedded container wiring |
| `src/test/java/.../Flows.java`, `CharacterizationTest.java` | the golden-master harness |

## Requirements

1. Move to `tomcat-embed-core` 10.1.x and the `jakarta.servlet` API.
2. Every characterization test stays green. Do not edit, delete or re-record the golden files.
3. Migrate what belongs to Jakarta EE and only that. Packages that belong to the JDK keep their
   `javax` names.
4. Look beyond import statements: anything in the code that names the old namespace.
5. `ANSWER.md`: what you changed, what you deliberately did not change and why, how the tests
   protected you, and what else would change on a real JBoss EAP 8 deployment (descriptors, the
   security subsystem, libraries that are still javax-based).

Using OpenRewrite (`org.openrewrite.java.migrate.jakarta.JavaxMigrationToJakarta`) is welcome; it
is not required, and the result is graded the same way.

## Acceptance criteria (what the grader checks)

- All eight characterization flows match the golden masters on Tomcat 10.1.
- No `javax.servlet` anywhere in `src/main` (imports or literals); Tomcat 9 gone from the pom.
- `javax.sql` and `javax.naming` are intact.
- Notes still persist; error pages keep their contract on the new container.
- `ANSWER.md` explains the namespace rules and the EAP 8 follow-ups.

## How to run

```bash
make setup      # JDK 21 + Maven, downloads artifacts once
make test       # characterization tests (green now; keep them green)
make run        # the service on :8080
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade modernize/w4-c1
make clean
```
