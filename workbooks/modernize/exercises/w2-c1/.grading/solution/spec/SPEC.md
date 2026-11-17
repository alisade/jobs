# claimdesk-web: current-state specification

Facts are in `spec/inventory.json` with file:line evidence; this document summarises them for the pod.

## 1. Context (C4 level 1)

```text
[Adjusters, supervisors, auditors] --HTTPS FORM login--> [ClaimDesk WAR on JBoss EAP 7.4]
[ClaimDesk] --LDAPS--> [Corporate LDAP]            (claimdesk.properties:2)
[ClaimDesk] --HTTP--> [Sentinel fraud scoring]      (datasource-claimdesk.cli:5)
[ClaimDesk] --SOAP--> [PAS 6 policy admin]          (claimdesk.properties:5)
[ClaimDesk] --SMTP--> [SIU mailbox]                 (MailNotifier.java)
[ClaimDesk] --JMS--> [Reserving]                    (PaymentServlet.java)
[ClaimDesk batch] --SFTP--> [Halberd Re]            (NightlyReinsuranceExport.java)
[ClaimDesk] --JDBC--> [Oracle CLMPRD]               (datasource-claimdesk.cli:2-3)
```

## 2. Containers and components (C4 levels 2-3)

| Container | Runs where | Components |
|---|---|---|
| claimdesk-web.war | EAP 7.4, cdk-app-01..04 | ClaimServlet, PaymentServlet, AdminServlet, LdapGroupFilter, StartupListener, DAOs, clients |
| EJB timer NightlyReinsuranceExport | inside the WAR, every node, non-persistent | bordereau to /var/claimdesk/outbox, SFTP push |
| cron purge-archive.sh | cdk-app-01 only, sqlplus | deletes from yearly archive tables |
| Oracle CLMPRD | DB tier | tables, sequences, PKG_RESERVE |

## 3. Data: database touchpoints

CLAIM (read), CLAIM_NOTE (insert), CLMARCH.CLAIM_ARCHIVE_<YYYY> (read by concatenated SQL, delete by
cron), RESERVE_LINE (update, read), PKG_RESERVE.RECALC (execute), CLAIMS.PAYMENT (insert, mapped only in
orm.xml), USER_ROLE and ADJUSTER (SQL in queries.properties), SEQ_NOTE, SEQ_PAYMENT. Easy to miss:
orm.xml, queries.properties, the archive name built at runtime, the cron script.

## 4. Security flows

FORM login against the PicketBox domain `claimdesk-ldap` (jboss-web.xml:4). Checks to preserve in OIDC:
CLAIMS_USER on everything and CLAIMS_ADMIN on /admin/* (web.xml), CLAIMS_SUPERVISOR for payments over
25000 (PaymentServlet), direct LDAP membership of cn=claims-payments for /payments/* (nested groups
ignored), AUDITOR in claim.jsp, REASSIGN_CLAIMS from USER_ROLE. Two sources of truth (LDAP and the DB)
must map to claims or stay as an app-side lookup.

## 5. Integrations and failure behaviour

Fraud scoring fails open (score 0 on any IOException). LDAP filter fails closed. SFTP disables host key
checking. Mail failures throw and abort the payment request after the fraud check. JMS send happens after
the DB writes, not in an XA guarantee you can see from the code (open question).

## 6. Runtime and deployment assumptions

Java 8; EAP 7.4; America/New_York; ISO-8859-1 default charset (JSP and bordereau too); Oracle dialect
(NVL, ROWNUM, SYSDATE); JNDI java:/jdbc/ClaimDeskDS pool 60; local /var/claimdesk and /etc/claimdesk.

## 7. Modernization risks and blast radius

| Change | Breaks | Detect with |
|---|---|---|
| EAP 8 | PicketBox domain removed; needs Elytron | deploy to an EAP 8 test node; login characterization test |
| Jakarta EE 10 | javax.servlet/jms/persistence/mail/xml.ws imports; keep javax.sql, javax.naming | compile; OpenRewrite dry run |
| JDK 21 | JEP 400 UTF-8 default vs ISO-8859-1 assumptions | byte diff of bordereau and JSP output |
| OIDC | the 25000 rule, direct-membership group, DB roles | authorization matrix tests before and after |
| Cluster | EJB timer runs on every node; cron on one host | logs per node; duplicate SFTP uploads |

## 8. Open questions and unverified claims

Prod JNDI bindings may differ from the 2019 cli script. DB grants for claimdesk_app vs claimdesk_batch.
Whether the JMS send is transactional with the DB writes. Who consumes the SIU mail. Whether Halberd Re
validates the bordereau charset.
