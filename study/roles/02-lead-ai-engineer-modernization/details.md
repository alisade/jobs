# Role 2: Lead AI Engineer, application modernization - details

Material for each item in [highlights.md](highlights.md). Shared topics (Claude Code skills, subagents,
hooks, MCP, evals, spec-driven development) live in the [shared core](../../shared/details.md) and are not
repeated here. Links were checked on 2026-11-13.

---

## 1. Enterprise Java modernization

**Why:** "strong preference for enterprise Java modernization experience involving JDK, JBoss/application
servers, deployments, Maven/Gradle and dependency remediation."

**Learn:**
- JDK upgrade path 8 to 11 to 17 to 21: removed modules (JAXB, JAX-WS, CORBA), strong encapsulation of
  internals, `--add-opens` as a smell, and GC and TLS default changes
- `javax.*` to `jakarta.*` (Jakarta EE 9+), and why it forces app server and library upgrades together
- JBoss EAP 7 to 8 / WildFly: what changes in deployment descriptors, security subsystem (Elytron), modules
- Maven: dependency tree, convergence, enforcer rules, BOMs, shading conflicts; Gradle equivalents
- Automated refactoring with OpenRewrite recipes; static migration analysis with Konveyor / Red Hat MTA
- How OS, JDK, app server, driver and library upgrades interact (TLS, charset, timezone, native libs)

**Links:**
- [Oracle JDK 21 migration guide](https://docs.oracle.com/en/java/javase/21/migrate/getting-started.html)
- [jdeps](https://docs.oracle.com/en/java/javase/21/docs/specs/man/jdeps.html)
- [jdeprscan](https://docs.oracle.com/en/java/javase/21/docs/specs/man/jdeprscan.html)
- [OpenRewrite docs](https://docs.openrewrite.org/)
- [OpenRewrite: migrate to Java 21](https://docs.openrewrite.org/recipes/java/migrate/upgradetojava21/)
- [OpenRewrite: javax to jakarta](https://docs.openrewrite.org/recipes/java/migrate/jakarta/javaxmigrationtojakarta/)
- [Eclipse Transformer (bytecode javax to jakarta)](https://github.com/eclipse-transformer/transformer)
- [Konveyor](https://konveyor.io/)
- [Red Hat Migration Toolkit for Applications](https://developers.redhat.com/products/mta/overview)
- [JBoss EAP 8.0 migration guide](https://docs.redhat.com/en/documentation/red_hat_jboss_enterprise_application_platform/8.0/html/migration_guide/index)
- [WildFly documentation](https://docs.wildfly.org/)
- [Maven dependency plugin](https://maven.apache.org/plugins/maven-dependency-plugin/)
- [Versions Maven plugin](https://www.mojohaus.org/versions/versions-maven-plugin/)
- [Maven enforcer plugin](https://maven.apache.org/enforcer/maven-enforcer-plugin/)
- [Gradle: viewing and debugging dependencies](https://docs.gradle.org/current/userguide/viewing_debugging_dependencies.html)

**Exercise:** Take spring-framework-petclinic (or Eclipse Cargo Tracker, a Jakarta EE app), run jdeps and
an OpenRewrite dry run, and write the upgrade plan before changing anything. Then execute it one step at a
time, with the tests green after each step.

---

## 2. Agentic reverse engineering into specs

**Why:** "Lead reverse engineering of legacy and current-state applications using AI agents/skills to
discover architecture, dependencies, integrations, database touchpoints, security flows, runtime
assumptions, and deployment characteristics," then "turn reverse-engineered findings into clear technical
specifications."

**You already have:** the habit of trusting live state over the repo (for example Jenkins `config.xml` vs
groovy in git, live ArgoCD CRs vs stale `.tf`). That is the core instinct of reverse engineering.

**Learn:**
- A discovery checklist an agent can run: entry points, modules, build files, config sources, DB access
  (JDBC/JPA/ORM mappings, raw SQL), outbound calls, auth checks, scheduled/batch jobs, deploy descriptors
- Fan-out with subagents per area, and a final spec where every claim cites a file and line
- C4 model for the output (context, containers, components)
- Static tools that keep the agent honest: ArchUnit rules, jQAssistant graphs, SchemaSpy for the database
- Writing the spec in a spec-driven format (see [shared section 7](../../shared/details.md#7-spec-driven-development))

**Links:**
- [C4 model](https://c4model.com/)
- [Structurizr docs](https://docs.structurizr.com/)
- [ArchUnit](https://www.archunit.org/)
- [jQAssistant](https://github.com/jqassistant)
- [SchemaSpy](https://schemaspy.org/)
- [Claude Code subagents](https://code.claude.com/docs/en/sub-agents)

**Exercise:** Write the `reverse-engineer` skill and run it on two unfamiliar open-source apps. Grade the
output by hand: how many claims were wrong or unsupported? Fix the skill and run it again. Keep the
failure log; the posting asks for exactly this ("capturing reusable patterns, failure modes, context
requirements").

---

## 3. LDAP to Okta, OAuth/OIDC/JWT

**Why:** "identifying LDAP/legacy authorization logic and guiding migration to token-based identity and
access patterns using Okta, OAuth/OIDC/JWT."

**You already have:** LDAP binds, AD groups, Kerberos and service-account behavior from the infra side.

**Learn:**
- Where legacy apps hide authorization: LDAP group lookups in code, container-managed security
  (`web.xml` roles), custom filters, DB role tables
- OIDC login for web apps vs JWT bearer validation for APIs (resource servers)
- Mapping LDAP groups to token claims (Okta groups claim), keeping role names stable so code changes stay small
- Okta with AD/LDAP as the source directory during transition
- Token pitfalls: audience and issuer checks, clock skew, key rotation, algorithm confusion

**Links:**
- [Spring Security: LDAP authentication](https://docs.spring.io/spring-security/reference/servlet/authentication/passwords/ldap.html)
- [Spring Security: OAuth 2.0 login](https://docs.spring.io/spring-security/reference/servlet/oauth2/login/core.html)
- [Spring Security: JWT resource server](https://docs.spring.io/spring-security/reference/servlet/oauth2/resource-server/jwt.html)
- [Okta: OAuth 2.0 and OIDC overview](https://developer.okta.com/docs/concepts/oauth-openid/)
- [Okta: customize tokens with a groups claim](https://developer.okta.com/docs/guides/customize-tokens-groups-claim/main/)
- [Okta Spring Boot starter](https://github.com/okta/okta-spring-boot)
- [ASP.NET Core JWT bearer authentication](https://learn.microsoft.com/en-us/aspnet/core/security/authentication/configure-jwt-bearer-authentication)
- [Keycloak docs (local OIDC provider for testing)](https://www.keycloak.org/documentation)
- [RFC 9700: OAuth 2.0 security best current practice](https://datatracker.ietf.org/doc/html/rfc9700)
- [RFC 8725: JWT best current practices](https://datatracker.ietf.org/doc/html/rfc8725)
- [RFC 7519: JSON Web Token](https://datatracker.ietf.org/doc/html/rfc7519)
- [Okta developer signup](https://developer.okta.com/signup/)

**Exercise:** Add LDAP login with two roles to the sample app (embedded LDAP server). Write tests that pin
who can do what. Migrate to Okta with a groups claim and show the same tests pass.

---

## 4. Safe change on monoliths

**Why:** "Preserving existing application architecture", "assess blast radius across databases,
interfaces, shared libraries, batch processes ... before changes are executed", and "rollback
considerations".

**You already have:** change management, backups before mutation, staged rollouts.

**Learn:**
- Characterization (golden master) tests: capture current behavior before touching anything
- Blast-radius inventory: callers, shared libraries, DB objects, batch jobs, config, pipelines
- Parallel change (expand/contract) and branch by abstraction for in-place upgrades
- Strangler fig, and when NOT to use it (the posting says do not decompose without a reason)

**Links:**
- [Characterization test](https://en.wikipedia.org/wiki/Characterization_test)
- [ApprovalTests](https://approvaltests.com/)
- [Working Effectively with Legacy Code (Feathers)](https://www.oreilly.com/library/view/working-effectively-with/0131177052/)
- [Parallel change](https://martinfowler.com/bliki/ParallelChange.html)
- [Branch by abstraction](https://martinfowler.com/bliki/BranchByAbstraction.html)
- [Strangler fig application](https://martinfowler.com/bliki/StranglerFigApplication.html)
- [Feature toggles](https://martinfowler.com/articles/feature-toggles.html)

**Exercise:** Before the JDK upgrade, write approval tests over 10 key HTTP flows. Then write a blast-radius
section in the spec: everything that could break and how you would detect it.

---

## 5. .NET Framework to modern .NET

**Why:** "Drive modernization of Java and .NET applications."

**Learn:**
- .NET Framework 4.x to .NET 8+: project format (SDK-style), `System.Web` gaps, WCF, config, Windows-only APIs
- Microsoft's tooling: the porting guide, Upgrade Assistant, and Copilot-based app modernization
- Running on Linux vs staying on Windows Server

**Links:**
- [Port from .NET Framework to .NET](https://learn.microsoft.com/en-us/dotnet/core/porting/)
- [.NET Upgrade Assistant overview](https://learn.microsoft.com/en-us/dotnet/core/porting/upgrade-assistant-overview)
- [GitHub Copilot app modernization for .NET](https://learn.microsoft.com/en-us/dotnet/core/porting/github-copilot-upgrade/overview)
- [eShopModernizing (legacy .NET Framework sample apps)](https://github.com/dotnet-architecture/eShopModernizing)

**Exercise:** Run the upgrade tooling on one eShopModernizing app and write up what it could not do.

---

## 6. Supply chain and vulnerability remediation

**Why:** Preferred: "vulnerability remediation, software supply-chain controls, secrets management."

**You already have:** pipeline security, secrets handling, policy hooks.

**Links:**
- [OWASP Dependency-Check](https://owasp.org/projects/dependency-check)
- [CycloneDX (SBOM standard)](https://cyclonedx.org/)
- [Syft (SBOM generator)](https://github.com/anchore/syft)
- [Grype (vulnerability scanner)](https://github.com/anchore/grype)
- [OSV (vulnerability database)](https://osv.dev/)
- [SLSA framework](https://slsa.dev/)
- [Renovate docs](https://docs.renovatebot.com/)
- [OWASP ASVS](https://asvs.owasp.org/)

**Exercise:** Generate an SBOM for the sample app before and after the upgrade, and produce a remediation
report showing CVEs fixed, CVEs remaining, and why.

---

## 7. Leading pods with agents

**Why:** "Break modernization work into pod-ready increments, assign work to developers, review agent
outputs" and "mentor developers in agentic engineering ... and human-in-the-loop verification."

**Learn:**
- Slicing: one increment means one verifiable outcome (tests green, deployable, revertible)
- Review rubric for agent PRs: claims vs evidence, scope creep, silent behavior changes, deleted tests
- Running agents headless in CI for repeatable steps, with humans at the gates
- Postmortems for agent failures, fed back into skills

**Links:**
- [Claude Code headless mode](https://code.claude.com/docs/en/headless)
- [Claude Code GitHub Actions](https://code.claude.com/docs/en/github-actions)
- [Google SRE book: postmortem culture](https://sre.google/sre-book/postmortem-culture/)

**Exercise:** Write the pod playbook for the portfolio project: increments, owner per increment, gates,
review rubric, and the failure-mode log format.
