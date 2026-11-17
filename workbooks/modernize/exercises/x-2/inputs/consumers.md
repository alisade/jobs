# Consumers of corvane-commons

| # | Consumer | Runtime | commons version | Uses | Team | Notes |
|---|---|---|---|---|---|---|
| 1 | ClaimDesk (claimdesk-web WAR) | EAP 7.4, JDK 8 (moving to 21, then EAP 8) | 2.14.3 | web, audit, rest, jms, db | ClaimDesk pod | modernization program in flight |
| 2 | PolicyHub WAR | EAP 8.0, JDK 17 | 2.14.3 via the Eclipse Transformer at build time | web, audit, rest | Policy team | transformer step is fragile, wants 3.0 |
| 3 | AgentPortal API WAR | EAP 7.4, JDK 11 | 2.13.0 | web, json, rest | Distribution team | no upgrade budget until Q3 |
| 4 | claims-batch-spring (Spring Boot 2.7 batch) | JDK 17, embedded Tomcat 9 | 2.14.3 | audit, json, db | ClaimDesk pod | Spring Boot 2.7 is javax; Boot 3 is jakarta |
| 5 | BillingSync (Spring Boot 3.2) | JDK 21 | 2.12.1 with exclusions | json only | Billing team | already jakarta; excludes commons-web |
| 6 | PolicyPortal.Api (.NET 10) | Linux containers | n/a | calls `/commons/v1/reference/*` on ClaimDesk and PolicyHub | Portal team | parses the ErrorJsonWriter JSON shape |
| 7 | Reporting extracts (Informatica) | n/a | n/a | reads AUDIT_EVENT, REF_CODE directly with SQL | Data team | SELECT * in two jobs |

Pipelines: each Java consumer builds with Jenkins, resolving commons from Nexus with version
ranges in 2 of them (`[2.0,)` in AgentPortal, `[2.12,3.0)` in BillingSync). Contract tests: none
between commons and consumers; PolicyPortal.Api has its own integration tests against a test
PolicyHub.
