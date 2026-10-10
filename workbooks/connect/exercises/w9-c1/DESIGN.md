# LFG help desk identity, access and compliance architecture

<!-- Audience: CISO office, LFG IT architecture board, the federal client's ISSO. Use inputs/.
Tables beat prose. Name the Connect features you rely on and their limits. -->

## 1. Requirements summary and key constraints

## 2. Agent and admin identity (SSO, MFA, lifecycle)

<!-- IdP per environment, SAML setup, MFA, joiner/mover/leaver into Connect users, break-glass. -->

## 3. Authorization model (RBAC, ABAC/TBAC, hierarchy)

<!-- Security profiles, access control tags (what they can scope, the limits), hierarchy-based
access, how Monterrey/Pune/HR/VIP restrictions are enforced, how you stop privilege escalation. -->

## 4. Multi-region and multi-instance considerations

<!-- ACGR replica, SAML sign-in, tags and profiles kept identical across Regions, what is
per-instance. Separate federal instance. -->

## 5. Caller identity verification tiers

<!-- Tiers by request risk; ANI match, knowledge factors, OTP, CLEAR, portal-authenticated chat;
how each plugs into the flow; what happens on failure; Voice ID status. -->

## 6. Federal desk: GovCloud, FedRAMP and personnel

<!-- Where it runs, feature gaps vs commercial and their impact, boundary, public trust,
US-persons enforcement, supervision on site. -->

## 7. Data protection and retention

<!-- Encryption/KMS, redaction (PCI), recordings/transcripts/CTR storage, retention per desk,
legal hold, destruction evidence. -->

## 8. Audit, monitoring and access reviews

## 9. Risks, decisions and open questions
