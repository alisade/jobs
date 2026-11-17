# claimdesk-web: current-state specification

<!-- Audience: the modernization pod that will move ClaimDesk to JDK 21 and JBoss EAP 8 / Jakarta EE 10,
and the AppSec reviewer for the LDAP to OIDC change. Every claim cites app/<path>:<line>; the
machine-readable version of the facts is spec/inventory.json. Tables beat prose. -->

## 1. Context (C4 level 1)

<!-- Who uses ClaimDesk and which external systems it talks to. A text diagram is fine. -->

## 2. Containers and components (C4 levels 2-3)

<!-- The WAR, the app server, the database, the batch pieces (in-server timer vs cron), and the main
components inside the WAR (servlets, filters, DAOs, clients). -->

## 3. Data: database touchpoints

<!-- Tables, sequences and procedures, read/write, who touches them. Call out the ones that are easy to miss. -->

## 4. Security flows

<!-- Authentication path, every authorization check and where it lives, what an LDAP to OIDC migration must preserve. -->

## 5. Integrations and failure behaviour

## 6. Runtime and deployment assumptions

## 7. Modernization risks and blast radius

<!-- What breaks on JDK 21, Jakarta EE 10 / EAP 8 and OIDC, and how a pod would detect each one. -->

## 8. Open questions and unverified claims

<!-- What you could not prove from the code alone, and who would know. -->
