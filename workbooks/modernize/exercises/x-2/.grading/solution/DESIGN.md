# corvane-commons 3.0 (Jakarta): blast radius and rollback

## 1. Change summary and decision

3.0 bundles three changes: the javax to jakarta API move, a JDK 17 baseline, and an irreversible DDL on
AUDIT_EVENT. Recommendation: split them. Publish 2.15 (javax) and 3.0 (jakarta) from one source tree for a
support period ending 2027-08-31, ship the TENANT_ID column as a separate DBA-run additive migration, and stop
consumers from running commons-schema migrations. Do not drop 2.x in ARCH-212.

## 2. Blast radius

| Asset / consumer | Impact of 3.0 as proposed | Severity |
|---|---|---|
| ClaimDesk WAR (EAP 7.4) | jakarta types do not load on EAP 7.4; must stay on 2.x until EAP 8 (April-May) | high if forced |
| PolicyHub (EAP 8) | can drop the Eclipse Transformer; benefits | low, positive |
| AgentPortal (EAP 7.4, `[2.0,)`) | next build resolves 3.0 silently, deploy fails on EAP 7.4; team frozen until July | high |
| claims-batch-spring (Boot 2.7) | javax world; 3.0 breaks AuditInterceptor and EntityManager types; stays on 2.x until Boot 3 | high if forced |
| BillingSync (Boot 3, `[2.12,3.0)`) | range blocks 3.0; json only; can move any time | low |
| PolicyPortal.Api (.NET) | consumes `/commons/v1/reference/*` and the error JSON; any shape change in ErrorJsonWriter breaks parsing | medium |
| Informatica extracts | `SELECT *` on AUDIT_EVENT: new column changes the column list | medium |
| AUDIT_EVENT DDL | NOT NULL DEFAULT on 410 M rows, run by whichever consumer starts first, at startup, outside a DBA window; irreversible | critical |
| Flyway history (shared) | consumers on 2.x see a V3_0 entry they do not know: `validate` fails on their next startup | high |
| JMS AUDIT.EVENTS | payload must stay compatible between 2.x and 3.x publishers | medium |
| jackson-bom 2.15.4 pin | 3.0 should not downgrade consumers already on newer Jackson (see w1-t1) | medium |

## 3. Sequencing

1. Fix version ranges (AgentPortal to `[2.13,3.0)`) and turn off `commons.flyway.enabled` in every consumer;
   the commons schema is migrated by its own pipeline job.
2. DBA window (Sunday 02:00-06:00): add `TENANT_ID NUMBER NULL` (metadata-only), backfill in batches,
   no NOT NULL yet. Data team updates the two `SELECT *` jobs.
3. Dual publish from one source: 2.15.0 (javax) and 3.0.0 (jakarta, via build-time transform or a jakarta
   source set), same tests on both. JSON and JMS shapes frozen by contract tests.
4. Consumers move on their own calendar: BillingSync and PolicyHub (March, before the 2027-03-22 freeze),
   ClaimDesk with EAP 8 (April-May), claims-batch with Boot 3, AgentPortal in July.
5. Contract: after the last consumer is on 3.x, stop 2.x (support end date), then add NOT NULL in a later window.

## 4. Detection per risk

| Risk | Before production | In production |
|---|---|---|
| wrong artifact resolved | `dependency:tree` gate in each consumer CI; enforcer bans commons 3.x on javax consumers | startup log prints commons version and namespace |
| jakarta on EAP 7.4 | consumer build matrix: every consumer against 2.15 and 3.0 | deploy health check |
| REST/JSON shape | consumer-driven contract tests from PolicyPortal.Api against both versions | 4xx/5xx and parse errors in the .NET API |
| DDL lock or duration | rehearsal on a prod-size copy; DBA sign-off | AWR, lock waits during the window |
| Flyway history mismatch | `flyway validate` for every consumer in CI | startup failure alert |
| extracts | Informatica dry run on the changed table | row counts and job status |
| JMS payload | round-trip tests 2.x to 3.x and back | DLQ depth on AUDIT.EVENTS |

## 5. Rollback per step

1. Ranges and Flyway flag: revert config. 2. DDL: additive and nullable, so no rollback needed; consumers
ignore the column; true rollback would be a restore, which is why NOT NULL waits. 3. Dual publish: stop
publishing 3.0; nobody is forced onto it. 4. Each consumer: redeploy its previous artifact (still on 2.x).
5. Contract step: only after every consumer passed 10 business days on 3.x.

## 6. Go / no-go gates

Per step: consumer matrix green, contract tests green, flyway validate green, DBA sign-off for any DDL, no
freeze in the window, the consumer owner's approval for their move, and a rollback tested in staging.

## 7. Open questions

Can the platform team support two artifacts for 6 months? Who owns the commons schema migrations after the
change? Does the Data team have a non-`SELECT *` version of the two jobs? Is TENANT_ID needed by any consumer
before July?
