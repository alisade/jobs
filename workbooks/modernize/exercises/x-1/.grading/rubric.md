# Rubric: modernize/x-1 ClaimDesk will not deploy on JBoss EAP 8
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 40 | points = 40 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: EAP 8 (like WildFly 25+) has no legacy security subsystem (PicketBox), so `/subsystem=security` does not exist (WFLYCTL0030) and the batch rolls back; the WAR's `<security-domain>claimdesk-ldap</security-domain>` then has nothing to bind to, so the deployment waits on a missing service and rolls back (WFLYCTL0412/0180); on EAP 8 that name must be an Undertow application-security-domain backed by Elytron. Vault expressions are gone too. Partial: "use Elytron" without the deployment link. Zero: rebuild the WAR. |
| 3 | Evidence and noise | 15 | Quotes the CLI failure, the server.log WFLYCTL0412 line and the rollback; identifies WFLYEE0007 (optional JSTL TLV components) and the datasource deprecation as noise unrelated to the failure. |
| 4 | Option mapping and production | 20 | Full: maps java.naming.provider.url/bindDN/bindCredential to dir-context + credential-reference, baseCtxDN/baseFilter to identity-mapping, rolesCtxDN/roleFilter/roleAttributeID/roleRecursion to attribute-mapping, PropertiesRoles to mapped-role-mapper, FORM via http-authentication-factory; verification plan: log in as one user per role on the test node and compare `request.isUserInRole` results with EAP 7.4, keep EAP 7.4 as rollback, mention the server migration tool / MTA as a cross-check and that the later OIDC move swaps the realm or uses the OIDC client subsystem. Partial: config only. |
Total: 100
