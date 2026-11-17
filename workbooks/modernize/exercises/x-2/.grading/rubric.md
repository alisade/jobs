# Rubric: modernize/x-2 Blast radius and rollback for corvane-commons 3.0
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 0 | Does not apply: review-only design exercise (grade.sh reports 0/0) |
| 2 | Blast radius completeness | 30 | Full: all seven consumers with the specific break (EAP 7.4 and Boot 2.7 cannot run jakarta; PolicyHub can drop the transformer; BillingSync's `[2.12,3.0)` range is safe but AgentPortal's `[2.0,)` would silently pull 3.0 on the next build; .NET parses the ErrorJsonWriter shape; Informatica `SELECT *` breaks or changes with the new column), plus shared assets: AUDIT_EVENT DDL run by every consumer's Flyway at startup (first one to start does an online DDL on 410 M rows, others race), Flyway history shared, JMS message format, jackson-bom pin. Partial: Java consumers only. |
| 3 | Sequencing and parallel change | 25 | Full: split the library change from the DB change; dual publish 2.x (javax) and 3.x (jakarta) from one source (or a jakarta classifier) for a defined support period; fix version ranges first; DDL expand as its own DBA-run migration with a nullable column (or default without NOT NULL rewrite), Flyway disabled in consumers for the commons schema; consumers move per their calendar (PolicyHub March, ClaimDesk with EAP 8, AgentPortal July); contract later. Partial: big-bang 3.0 with a rollout order. |
| 4 | Detection and rollback | 25 | Full: contract tests for the REST/JSON shape run by the .NET team, a consumer build matrix against both artifacts, Flyway validate in CI, an Informatica dry run, dependency:tree checks for ranges; rollback per step (redeploy previous artifact; stop publishing; the DDL rollback is a restore so it is made additive and backward compatible instead). Partial: "roll back the release". |
| 5 | Gates and pushback | 20 | Full: go/no-go gates per step (consumer matrix green, contract tests green, DBA sign-off, no freeze), and explicit pushback on ARCH-212: do not drop 2.x yet, do not ship DDL inside the library release, do not run shared-schema migrations from every consumer. Partial: gates without pushback. |
Total: 100
