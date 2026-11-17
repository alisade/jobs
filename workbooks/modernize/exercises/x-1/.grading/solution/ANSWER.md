# ANSWER: modernize/x-1 ClaimDesk will not deploy on JBoss EAP 8

## Approach

Read the CLI output first, then the deployment error, then compared the old security domain with what the
EAP 8 node offers (`read-children-types` on elytron, config/eap8-existing.txt).

## Root cause

The CLI batch fails at step 1: `WFLYCTL0030: No resource definition is registered for address
[("subsystem" => "security")]`. EAP 8 removed the legacy security subsystem and PicketBox login modules,
and the vault (`${VAULT::...}`) with them. Because nothing was created, the WAR's
`<security-domain>claimdesk-ldap</security-domain>` has nothing to bind to: server.log shows
`WFLYCTL0412: Required services that are not installed: jboss.security.security-domain.claimdesk-ldap`
and the deploy is rolled back. The WAR is not the problem; WFLYEE0007 (optional JSTL TLV components) and
the datasource deprecation warning are unrelated noise.

## Fix

Elytron, in one batch then reload: dir-context (same ldaps URL and bind DN, password from credential
store claimdesk-cs alias ldap-bind); ldap-realm with rdn-identifier=uid under ou=people and an
attribute-mapping for groups (`(member={1})` under ou=groups, from cn, to Roles, role-recursion=2, matching
roleRecursion=2); simple-role-decoder on Roles; mapped-role-mapper with the four mappings from
claimdesk-roles.properties; security-domain; FORM http-authentication-factory; and an Undertow
application-security-domain named claimdesk-ldap, so the WAR deploys unchanged. `make check` is clean.

## Trade-offs / what I would do in production

On the test node, log in as one user per role (and one nested-group user) and compare role checks with
EAP 7.4 before cutover; keep EAP 7.4 as rollback. Cross-check with the server migration tool. When the
app moves to OIDC later, this domain is replaced by the OIDC client configuration, and the role mapping
moves to the token's groups claim (w3-c1).
