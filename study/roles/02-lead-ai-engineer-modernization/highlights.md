# Role 2: Lead AI Engineer, application modernization - highlights

Posting: [posting.md](posting.md). Full material: [details.md](details.md).
Do the [shared core](../../shared/highlights.md) first.

## Where you start

| Posting asks for | You already have |
|---|---|
| Production incident / P1 experience, disciplined systems thinking | 26 years of it |
| Enter an unfamiliar codebase and find where to look | Your daily work across many repos, accounts and clusters, often where the live state differs from the repo |
| Building or materially configuring agents/skills, Claude Code preferred | A substantial personal Claude Code harness: skills, hooks, MCP, permission rules |
| Human approval and verification points | Approval gates, backups before mutation, pre-push policy hooks |
| Linux/Red Hat and Windows, OS/middleware/library interactions | Deep ops experience on both |
| CI/CD, Git, logging, observability, secure delivery | Your day job |
| LDAP-based authN/authZ | AD, ADSI/LDAP binds, Kerberos and service accounts from the infra side |
| Okta, OAuth/OIDC/JWT | Federation concepts (SAML, OIDC trust for CI and cloud roles) |

**Fit:** strong on the "lead" half, meaning triage, blast radius, incidents, agent workflows and verification.
The open question is the "7-10 years as a Software Engineer" with "deep Java and/or .NET" experience,
especially enterprise Java modernization (JDK, JBoss, Maven). That is the gap to close and to frame
honestly: you lead and verify modernization; you are not yet a 10-year Java developer. A public
modernization repo is the best way to back that up.

## Gaps, most important first

1. **Hands-on enterprise Java modernization.** JDK 8 to 17/21, `javax` to `jakarta`, JBoss EAP 7 to 8,
   Maven/Gradle dependency remediation, OpenRewrite.
2. **Agentic reverse engineering and spec writing.** Skills and subagents that map architecture,
   dependencies, DB touchpoints and auth flows, then write a spec a pod can execute.
3. **LDAP to Okta migration in code.** Find legacy authorization logic and map LDAP groups to token
   claims, using Spring Security and ASP.NET Core patterns.
4. **Safe change on monoliths.** Characterization tests, blast-radius analysis, parallel change, rollback.
5. **.NET Framework to modern .NET.** Upgrade paths, tooling, and what breaks.
6. **Supply chain and vulnerability remediation.** SBOMs, scanners, upgrade policy.
7. **Leading pods.** Slicing work into agent-ready increments, reviewing agent output, mentoring.

## Plan (after the shared core)

| Week | Focus | Output |
|---|---|---|
| 1 | JDK and Jakarta migration mechanics; jdeps, jdeprscan, OpenRewrite | A legacy sample app upgraded to Java 21 with a written change log |
| 2 | Reverse-engineering skills: architecture, dependency, DB and auth discovery | A `reverse-engineer` skill that writes a C4-style spec |
| 3 | LDAP to OIDC: embedded LDAP baseline, then Okta (or Keycloak) with JWT and a groups claim | The same app authenticating via Okta, with roles preserved |
| 4 | Characterization tests, blast radius, rollback; app server (WildFly/JBoss) deploy | A test harness that proves behavior did not change |
| 5 | .NET upgrade path on a legacy sample; supply-chain tooling | An SBOM plus a remediation report |
| 6 | Package it: skill repo, pod playbook, demo | A public repo plus a 10-minute walkthrough |

## Portfolio project: "modernization pod kit"

Use a legacy open-source Java app as the target, for example the pre-Spring-Boot
[spring-framework-petclinic](https://github.com/spring-petclinic/spring-framework-petclinic) WAR, and add
LDAP login to it first using Spring Security's embedded LDAP server. Then build and publish:

1. A `reverse-engineer` skill. It produces an architecture spec covering modules, dependencies, DB tables
   touched, the auth flow, config and deploy shape, with every claim pointing to a file and line.
2. A `dependency-upgrade` skill. It runs jdeps/OpenRewrite, upgrades in small verified steps, and stops
   for approval at each major bump.
3. An `ldap-to-oidc` skill. It inventories authorization checks, maps groups to claims, migrates the app
   to Okta with JWT, and keeps role behavior identical.
4. Characterization tests that run before and after every step.
5. A pod playbook: how a lead slices the work, which checkpoints need a human, and a failure-mode log
   recording where the agent went wrong and how the skill was fixed.

This answers most of the posting directly, including the "Java/.NET experience" question, with evidence.

## Pitch

"I triage unfamiliar systems for a living. Now I encode that triage into agent skills, so a pod can
modernize an application safely, with every claim verified and every risky step behind a human gate."
