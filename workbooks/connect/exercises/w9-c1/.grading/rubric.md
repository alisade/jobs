# Rubric: connect/w9-c1 Identity, access and compliance architecture
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 0 | Does not apply: review-only design exercise (grade.sh reports 0/0) |
| 2 | Boundaries and federal | 20 | Full: separate GovCloud (US-West) instance/account for the federal desk; names the GovCloud feature gaps that matter and designs around them; FedRAMP Class D (formerly High); public trust as a suitability determination enforced through IdP groups; US-persons and on-site constraints. Partial: GovCloud named without gaps. Zero: federal contacts in the commercial instance. |
| 3 | Agent identity and lifecycle | 15 | Full: SAML with correct relay state/RoleSessionName/GetFederationToken scoping, 12 h session behaviour, provisioning from IdP groups (joiner/mover/leaver), break-glass that works when the IdP is down. Partial: SSO only. |
| 4 | Authorization model | 25 | Full: security profiles + tag-based access control with its real limits (4 tags AND, 7 profiles OR, untagged overrides) + hierarchy-based access for users; Monterrey/Pune/HR/VIP/supervisor rules each mapped to a mechanism; privilege-escalation guard. Partial: RBAC only or TBAC without limits. Zero: one admin profile for all. |
| 5 | Caller verification | 20 | Full: tiers by request risk; OTP to the phone on record (not the calling number); CLEAR for strongest proofing using its documented Connect pattern; authenticated portal chat via a validated signed token; Voice ID end of support acknowledged; failure routes to an agent with the verification level. Partial: one-size verification. |
| 6 | Data protection, retention, audit | 20 | Full: KMS per desk, recordings/transcripts/CTR stores with retention per schedule, Object Lock + legal hold, PCI by not storing card data (pause/redact), audit of recording access and config changes, recertification. Partial: encryption only. |
Total: 100
