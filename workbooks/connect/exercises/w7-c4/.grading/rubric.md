# Rubric: connect/w7-c4 CRM/ITSM integration: ServiceNow vs Salesforce
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 0 | Does not apply: review-only design exercise (grade.sh reports 0/0). |
| 2 | Option analysis accuracy | 25 | Full: correctly distinguishes the Amazon Connect CTI Adapter for Salesforce (managed package + serverless app in the customer's account, customer-owned instance) from Service Cloud Voice bundle (Salesforce-provisioned instance in a Salesforce-managed account) and SCV with partner telephony / bring your own Amazon Connect (customer-owned instance); is accurate about ServiceNow (AWS documents Customer Profiles AppFlow mapping and the agent assist knowledge connector; ServiceNow builds its own Connect CTI; custom Table API integration). Partial: options listed but ownership/billing/data-location wrong. Zero: invents an AWS ServiceNow CTI product or misstates who owns the instance. |
| 3 | Requirements traceability | 15 | Every recommendation traced to R1-R10; R6/R7 recognized as eliminating the SCV bundle; a scored comparison. |
| 4 | Ticket logging design | 20 | Idempotency key (ContactId / InitialContactId), conditional write or external id, event-driven source (EventBridge contact events, contact records), retries/DLQ, reconciliation, 7-year traceability, links not copies of media. |
| 5 | Security and multi-LOB on one instance | 15 | SAML SSO via Okta, tag-based access control / security profiles per LOB, least-privilege integration users, secrets management, PII kept out of attributes for HR. |
| 6 | Operability and risk | 15 | Ownership after hypercare matched to a 6-person team, upgrade coupling (managed package, ServiceNow families), blast radius of a shared instance, POC plan, open questions that a review board would actually ask. |
| 7 | Communication | 10 | Clear diagram, end-to-end walkthrough for one IT and one HR contact, ADR with consequences, concise. |
Total: 100
