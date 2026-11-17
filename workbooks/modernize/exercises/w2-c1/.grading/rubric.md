# Rubric: modernize/w2-c1 Reverse-engineer claimdesk-web
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 55 | points = 55 * passed / total from grade.sh |
| 2 | SPEC.md usable by a pod | 20 | Full: C4 context and containers (including the cron host as a separate runtime), data section that calls out the orm.xml table, the properties-file SQL, the per-year archive tables and the PL/SQL package; security flows that list all six checks and say what OIDC must preserve (CLAIMS_SUPERVISOR threshold, direct-membership LDAP group, DB-held REASSIGN_CLAIMS); claims cite file:line. Partial: a list of facts without structure or risk. |
| 3 | Risks and blast radius | 15 | Full: ties concrete evidence to concrete breakages: PicketBox security domain gone in EAP 8, javax to jakarta (servlet, JMS, JPA, mail, ws) but not javax.sql/javax.naming, ISO-8859-1 vs JEP 400, the fail-open fraud check, StrictHostKeyChecking=no, the cron running only on cdk-app-01, EJB timer non-persistent in a cluster. Each with a detection method. Partial: generic "test everything". |
| 4 | Method and honesty | 10 | Full: ANSWER.md describes a repeatable discovery checklist (or skill/subagent split) and how claims were verified; open questions list what static reading cannot prove (prod JNDI bindings, DB grants, traffic). Partial: no verification step. |
Total: 100
