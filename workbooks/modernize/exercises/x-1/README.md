# modernize/x-1 - ClaimDesk will not deploy on JBoss EAP 8: the legacy security domain

**Type:** troubleshooting (optional add-on) | **Estimate:** 1.5 hours | **Study plan:** Week 7 add-on (EAP 8 security) and Week 4 (app server targets)

## Symptom

The first ClaimDesk deployment to a JBoss EAP 8 test node (CHG-88302) failed and was rolled back.
The CLI script copied from the EAP 7.4 build failed, and the Jakarta EE 10 WAR (green on WildFly in
CI) would not deploy. A developer suspects the WAR. Security wants the same LDAP, the same groups,
the same roles, and no secrets in the script. Read `evidence/PAGE.txt` first.

There is no EAP server here: `make check` is a static dry run of the CLI script against a model of
the target (which subsystems exist and what is already configured, `config/eap8-existing.txt`).

## What you have

| Path | What it is |
|---|---|
| `evidence/` | the change thread, the CLI output, a server.log excerpt (trimmed) |
| `config/standalone-eap74-security.xml` | the EAP 7.4 legacy security domain ClaimDesk logs in through today |
| `config/claimdesk-roles.properties` | the LDAP group to role mapping used on EAP 7.4 |
| `config/eap8-existing.txt` | what already exists on the EAP 8 node (a credential store with the LDAP bind alias, defaults) |
| `config/migrate-security.cli` | the script that failed (yours to rewrite) |
| `deploy/WEB-INF/jboss-web.xml` | the WAR's descriptor |
| `tools/cli_lint.py` | the dry-run checker behind `make check` |

## Your task

1. Root cause with evidence: why the script fails, why the deployment fails, and whether the WAR
   is to blame. Separate the noise in the log from the failure.
2. Rewrite `config/migrate-security.cli` for Elytron so the application keeps authenticating
   against the same directory and gets exactly the same roles: users found the same way, groups
   found the same way (including nested groups), the same group-to-role mapping, FORM login, and the
   bind password from the existing credential store. Use `batch` ... `run-batch`, then `reload`.
3. Keep the WAR unchanged if you can, and say why that works.
4. Write `ANSWER.md`: Approach, Root cause, Fix (and how you verified it), Trade-offs / production follow-ups.

## Acceptance criteria (what the grader checks)

- `make check` is clean: only subsystems EAP 8 has, every reference resolves, no vault expressions.
- Hidden checks of the Elytron resources: dir-context (same URL, bind DN, credential store alias),
  ldap-realm (uid under ou=people; groups by `(member={1})` under ou=groups, `cn`, recursion 2), role
  decoder, the four role mappings, security domain wiring, a FORM http-authentication-factory, and an
  Undertow application-security-domain with the name the WAR uses.
- `ANSWER.md` explains the subsystem removal and the mapping from each old module option.

## How to run

```bash
make setup
make check      # dry run of the CLI script
make test       # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade modernize/x-1
make clean
```
