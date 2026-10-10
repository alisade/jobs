# ANSWER: connect/w9-c1 Identity, access and compliance architecture

## Approach

Split the problem by boundary first (enterprise commercial vs federal FedRAMP High), then by
who may see what (site, tier, HR, VIP, supervisors), then by caller risk, then by data class.

## Fix

- Separate GovCloud (US-West) instance and account for the federal desk, with the feature gaps
  designed around (no AI agents, Cases, Customer Profiles, conversational analytics AI).
- SAML everywhere, Okta-driven provisioning of Connect users, profiles, hierarchy and tags.
- RBAC security profiles + tag-based access control (within its 4-tag/7-profile limits) +
  hierarchy-based access for supervisors, with the escalation guard.
- Tiered caller verification: ANI, knowledge factor, OTP to phone on record, CLEAR for tier 3,
  signed portal token for chat; Voice ID is end of support.
- KMS per desk, Object Lock retention per schedule, PCI by never storing card data.
- Audit through CloudTrail, agent activity audit, IaC-only admin changes, recertification.

## Trade-offs / what I would do in production

Prove TBAC scoping with a test matrix per profile before go-live (it fails open on untagged
overlap). Confirm with the federal ISSO which IdP and which Bedrock models (if any) are allowed.
