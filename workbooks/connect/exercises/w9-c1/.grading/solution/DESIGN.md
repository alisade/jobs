# LFG help desk identity, access and compliance architecture

## 1. Requirements summary and key constraints

- Two desks with different boundaries: LFG enterprise (commercial Regions, ACGR) and a federal
  desk that needs a FedRAMP High (now "Class D") boundary, US persons with public trust.
- Least privilege by site: Monterrey Tier 1 only, Pune no live contacts and no federal data,
  supervisors scoped to their teams, HR and VIP queues restricted.
- Credential resets are the top social-engineering vector: verification must scale with risk.
- PCI: no card data at rest; SOX/federal retention schedules; full audit of access and changes.

## 2. Agent and admin identity (SSO, MFA, lifecycle)

| Item | Decision |
|---|---|
| Identity type | SAML 2.0 on every instance (fixed at creation; also an ACGR prerequisite) |
| IdP | Okta (LFG) for both desks; agents are LFG employees. The federal instance gets its own Okta app, MFA = phishing-resistant (Okta FastPass / PIV-backed where the client requires) |
| SAML wiring | IdP-initiated, relay state `https://<region>.console.aws.amazon.com/connect/federate/<instance-id>` (GovCloud: `https://console.amazonaws-us-gov.com/connect/federate/<instance-id>`), RoleSessionName = Connect username, role allows only `connect:GetFederationToken` on `.../instance/<id>/user/${aws:userid}` |
| Sessions | Connect sessions end 12 h after login; Okta session policy aligned; authentication profiles for IP restrictions on admin access |
| Lifecycle | Workday -> Okta groups -> a provisioning Lambda (or Terraform pipeline) creates/updates/deletes Connect users with security profiles, routing profile, hierarchy group and access control tags from group membership; leaver = disable in Okta + delete Connect user within 1 h |
| Admin | Admins use a separate privileged Okta app with step-up MFA. Break-glass: on a SAML instance every sign-in goes through the IdP, so an IdP outage locks admins out; keep a sealed IAM role with Connect administrative API permissions (used from the AWS console/CLI), alarmed on use |

## 3. Authorization model (RBAC, ABAC/TBAC, hierarchy)

RBAC: security profiles per role (Agent-Tier1, Agent-Tier2, Agent-VIP, Agent-HR, Supervisor,
Admin, QA-Evaluator, L2-ReadOnly).

ABAC (tag-based access control): access control tags on security profiles scope queues, routing
profiles and users in the admin website, and via IAM `aws:ResourceTag` conditions other resources;
real-time and historical metrics, agent activity audit, dashboards, evaluations and cases honour
them. Limits: up to 4 access control tags per profile (AND), up to 7 tagged profiles per user
(OR), and an untagged profile overrides on overlap, so restricted users must never also hold an
untagged profile.

| Tag key | Values | Applied to |
|---|---|---|
| `lfg:desk` | enterprise, federal | queues, routing profiles, users (federal is a separate instance anyway) |
| `lfg:tier` | t1, t2, vip, hr | queues, routing profiles |
| `lfg:site` | clt, mty | users |

- Monterrey supervisors: profile tags `lfg:tier=t1` AND `lfg:site=mty`.
- HR queue: only Agent-HR (tag `lfg:tier=hr`); Contact search and recordings for HR contacts
  restricted via the same tags.
- Supervisors: hierarchy-based access control (only resource: users, own group and descendants)
  for team scoping plus TBAC for queues.
- Escalation guard (AWS best practice): apply TBAC to all resources together, remove "edit
  security profiles" and list-leaking pages (flows, modules, prompts, rules, contact search) from
  non-admin profiles, so a tagged admin cannot create an untagged profile.
- Pune L2: no Connect console access at all; ServiceNow role only. Developers deploy through the
  pipeline (IAM roles), never the admin website in prod.

## 4. Multi-region and multi-instance considerations

- Enterprise: us-east-1 primary, ACGR replica us-west-2 (supported pair). Users, security
  profiles, tags and routing config replicate with the instance; agent distribution set in the
  traffic distribution group; ACGR uses its own SAML sign-in endpoint, so agents get the ACGR
  sign-in in the Okta app and a runbook for failover.
- Federal: a separate instance in AWS GovCloud (US-West), separate AWS account in the GovCloud
  partition, separate Okta app; no cross-boundary data flows except anonymised metrics if the ISSO
  approves.

## 5. Caller identity verification tiers

| Tier | Requests | Checks | Mechanism |
|---|---|---|---|
| 0 | ticket status, outage info | none or ANI match | Lambda: ANI -> Okta/Workday phone on record |
| 1 | general support, software requests | ANI match + employee id + one knowledge factor | Lex slots + Lambda against Workday |
| 2 | password / MFA reset, access changes | OTP to the phone on record via AWS End User Messaging SMS (or Okta Verify push), never to the calling number unless it matches the record | Lambda + flow branch; fail -> agent with "unverified" flag, no self-service reset |
| 3 | VIP/executive requests, MFA reset for admins, federal account changes | identity proofing with CLEAR: the flow starts a CLEAR session and sends the verification link by SMS; the caller verifies on their phone while on the call; result routes the contact; agents can trigger step-up mid-call | CLEAR's documented Amazon Connect integration |
| portal | chat started from the Okta-authenticated portal | portal passes a short-lived signed token as a contact attribute at chat start; Lambda validates signature, audience and expiry | treated as tier 2 for chat |

Voice ID reached end of support on 2026-05-20, so no voice biometrics; partner options only after
a fraud review. Failed verification never blocks service: it routes to an agent with the
verification level in the contact attributes and the screen pop.

## 6. Federal desk: GovCloud, FedRAMP and personnel

- Connect Customer is in FedRAMP Class D (formerly High) scope in GovCloud (US-West only).
- Gaps vs commercial that change the design: no AI agents, no Agentic CX designer, no Email, no
  Cases, no outbound campaigns, no Customer Profiles, no conversational analytics AI features,
  no live media streaming. So: Lex-based self-service only (Lex V2 is in GovCloud US-West),
  ServiceNow (the client's FedRAMP instance) for case data, no generative summaries; Bedrock in
  GovCloud only if the model and its authorization level are approved by the ISSO.
- Personnel: public trust (moderate risk) for every agent and admin with access; it is a
  suitability determination, not a clearance; positions designated with OPM's tool; US persons.
  Enforced by Okta group membership fed from the HR clearance record, and the federal instance's
  users are provisioned only from that group.
- On-site supervision in Woodlawn: authentication profile IP restriction to the site and the VPN.

## 7. Data protection and retention

| Data | Store | Protection | Retention |
|---|---|---|---|
| Recordings | S3 (instance storage config) | SSE-KMS customer managed key per desk, bucket policy deny non-TLS, Object Lock compliance mode | enterprise SOX desks 7 y, others 1 y; federal 3 y then destroy with a deletion report |
| Transcripts/analytics | S3 | redacted output only exposed to analysts; originals in a restricted prefix | same as recordings |
| CTRs/events | Kinesis -> Firehose -> S3 data lake | PII minimised, partitioned by desk | 2 y enterprise analytics, federal per contract |
| Card data | never stored | PCI: pause recording or route card capture to a PCI-compliant IVR/Lambda path, redaction enabled, no card fields in ServiceNow | n/a |

Legal hold: Object Lock legal hold on specific prefixes; lifecycle rules handle expiry; quarterly
evidence of destruction for federal.

## 8. Audit, monitoring and access reviews

CloudTrail (organization trail, data events for the recordings bucket), agent activity audit,
Connect admin changes through IaC only with PR review; alarms on security profile changes, new
untagged profiles, IAM role changes; quarterly access recertification of security profiles and
access control tags from Okta groups; recording access logged and reviewed monthly.

## 9. Risks, decisions and open questions

- D1 separate GovCloud instance and account for the federal desk.
- D2 TBAC + hierarchy instead of per-site instances for enterprise.
- D3 tiered verification with CLEAR for tier 3; no voice biometrics.
- Risk: untagged profile overlap silently widens access -> automated check in CI.
- Open: will the client accept LFG Okta as IdP or require their PIV IdP? Which Bedrock models (if
  any) are authorized in their boundary? Federal records schedule details.
