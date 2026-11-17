# ClaimDesk modernization: scope for the pod (Q1 2027)

Application: ClaimDesk, Corvane Mutual's claims monolith. One Maven reactor, 9 modules, about
410k lines of Java, deployed as one WAR plus two batch jars on JBoss EAP 7.4 (RHEL 7, JDK 8).
Current-state spec: from the reverse-engineer run (see w2-c1); 14 tables, 6 integrations,
6 authorization checks, 2 scheduled jobs.

Target, all three in this program:

1. JDK 8 to JDK 21 on RHEL 9 (infrastructure retires the RHEL 7 hosts on 2027-03-31).
2. JBoss EAP 7.4 to EAP 8.0: Jakarta EE 10 (javax to jakarta), Elytron replaces PicketBox,
   Hibernate 6.
3. Authentication from LDAP (PicketBox LDAP login module plus a custom group filter) to Okta
   OIDC, roles from the groups claim, behaviour identical (see w3-c1).

Out of scope: microservices, a new UI, database changes beyond grants. The architecture board
wants the monolith to run safely on the target platform, not to be redesigned.

Known module facts:

| Module | Notes |
|---|---|
| claimdesk-core | domain, DAOs, 60% of tests |
| claimdesk-web | servlets, filters, JSP, web.xml |
| claimdesk-rating | reinsurance rating; partner golden files (Halberd Re) |
| claimdesk-intake | FNOL batch (see w1-t1) |
| claimdesk-reporting | month-end IBNR batch; actuarial close dependency |
| claimdesk-auth | LDAP role resolver, to be replaced |
| claimdesk-notes | notes service, embedded container in tests |
| corvane-commons (shared, separate repo) | used by 6 other applications; javax types in its public API |
| claimdesk-dist | assembly, jboss-cli scripts |
