# Reference: modernize/x-1

Model script: `.grading/solution/config/migrate-security.cli`.

Cause: JBoss EAP 8 removed the legacy security subsystem and PicketBox login modules (and the vault). The
copied script targets `/subsystem=security`, which does not exist (WFLYCTL0030), so the batch rolls back.
The WAR still names `claimdesk-ldap` in jboss-web.xml; with no legacy domain and no Undertow
application-security-domain of that name, the deployment's dependency is missing (WFLYCTL0412) and it
rolls back. The WAR is fine: define `/subsystem=undertow/application-security-domain=claimdesk-ldap` and keep it.

Mapping: provider.url, bindDN, bindCredential to dir-context (credential-reference to claimdesk-cs/ldap-bind);
baseCtxDN + baseFilter to identity-mapping (rdn-identifier=uid, search-base-dn); rolesCtxDN, roleFilter,
roleAttributeID, roleRecursion to attribute-mapping (filter-base-dn, filter, from=cn, to=Roles,
role-recursion=2); PropertiesRoles to mapped-role-mapper; simple-role-decoder turns the Roles attribute into
roles; security-domain ties them together; FORM through an http-authentication-factory.

Noise: WFLYEE0007 for JSTL TLVs is a long-standing harmless warning; the datasource attribute deprecation is
unrelated.
