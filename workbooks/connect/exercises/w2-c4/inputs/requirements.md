# LFG Help Desk Transformation - requirements (signed off by the steering committee 2026-10-02)

## Business outcomes (12 months after go-live)

- B1 Cost per contact down 25% (from ~USD 14.20).
- B2 Voice service level 85% in 30 s; chat 90% in 60 s; abandon < 5%.
- B3 Self-service containment 30% for password reset/unlock and VPN how-to (voice + chat).
- B4 FCR proxy >= 85%; CSAT >= 4.3.
- B5 One view of the employee's contact history across voice, chat and portal, inside ServiceNow.
- B6 Retire Avaya before the renewal decision (2027-03-31) and Genesys chat before 2027-06-30.

## Functional

- F1 Identify the employee on every contact (ANI match to the HR directory, employee portal SSO
  context for chat) and pass the verified identity and context to the agent.
- F2 Step-up identity verification for privileged requests (password reset for admins, MFA reset).
- F3 Self-service: password reset/unlock with push verification, VPN and MFA how-to, ticket status.
- F4 Callback offer when the predicted wait exceeds 3 minutes (keep place in queue).
- F5 VIP (executives and their assistants) priority routing to the VIP desk.
- F6 Major-incident mode: announcement in IVR and chat, deflection to status page, outbound notifications.
- F7 Screen pop and automatic incident creation/lookup in ServiceNow; contact summary in work notes.
- F8 English and Spanish for voice and chat.
- F9 Supervisor real-time dashboards; QA on 100% of contacts with sentiment and compliance flags.

## Non-functional

- N1 Availability 99.9% during business hours; major-incident line 24x7.
- N2 Disaster recovery: RTO 15 minutes for voice, RPO 0 for configuration (IaC), recordings RPO 1 hour.
- N3 Data residency: contact data and recordings stay in US Regions.
- N4 Retention: recordings and transcripts 13 months; contact records 25 months; incidents 7 years (ServiceNow).
- N5 Security: agent SSO via Okta (SAML), MFA; least privilege for admins; audit trail of config changes.
- N6 Accessibility: WCAG 2.2 AA for chat; TTY/relay support for voice.
- N7 Everything as code (CDK or Terraform), CI/CD with environments dev/test/prod.
