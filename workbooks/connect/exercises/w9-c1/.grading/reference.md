# Reference: connect/w9-c1

Model answer: `.grading/solution/DESIGN.md`. What great looks like:

- The federal desk is a separate instance in AWS GovCloud (US-West), separate account and IdP
  app, because the boundary is FedRAMP High (Class D) and data must not cross it; the design
  explicitly works around GovCloud gaps (no AI agents, Agentic CX, Email, Cases, outbound
  campaigns, Customer Profiles, conversational analytics AI features, live media streaming).
- Tag-based access control is used with its real limits (4 access control tags per security
  profile, AND; 7 tagged profiles per user, OR; an untagged profile overrides), combined with
  hierarchy-based access control (users only), plus the AWS guidance to disable list-leaking
  pages and apply TBAC to all resources together to prevent escalation.
- SAML details: relay state federate URL (GovCloud uses the console.amazonaws-us-gov.com host),
  RoleSessionName = Connect username, `connect:GetFederationToken` on `user/${aws:userid}`,
  sessions end 12 h after login.
- Verification is tiered by request risk; CLEAR's documented Connect integration (SMS link,
  verify on the phone during the call, step-up from the agent) for the riskiest requests; OTP to
  the phone of record; Voice ID is gone (end of support 2026-05-20).
- Retention and audit are per data class and per desk, with Object Lock and destruction evidence.
