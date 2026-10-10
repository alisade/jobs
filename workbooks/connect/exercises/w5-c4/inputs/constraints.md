# Constraints and non-functional requirements

1. ServiceNow is the system of record for incidents, requests and knowledge (kb_knowledge, 2,400
   published articles; 140 are HR, Legal or Finance restricted via ServiceNow user criteria).
2. InfoSec: no PII beyond employee ID and first name in model prompts; HR/Legal/Finance restricted
   content must never reach unentitled employees or contractors (12% of the workforce); prompt
   injection testing before go-live; model invocation logs treated as confidential.
3. Records: transcripts and recordings retained 13 months (SOX scope for Finance callers), then deleted.
4. Data residency: US regions only (us-east-1 primary, us-west-2 DR). No cross-border inference profiles.
5. Identity: Okta workforce SSO for agents; employees authenticated in the portal (Okta) or in the IVR by
   ANI match + employee ID + OTP to the MFA device; voice biometrics are not an option.
6. Latency: voice self-service turn must answer within Connect's synchronous Lambda limit (8 s);
   target p95 < 3 s perceived silence.
7. Accessibility: chat widget WCAG 2.2 AA; voice prompts plain language, DTMF alternative on every menu.
8. Go-live in 16 weeks, phased; offshore team (Pune) builds flows and Lambdas, onshore lead owns design
   reviews and production readiness.
9. Budget owner wants a cost per contact model before approving AI features.
