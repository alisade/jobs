# LFG help desk: identity, access and compliance requirements (security workshop, 2026-09-24)

## Organisations and environments

| Desk | Users served | Volume | Platform target | Constraints |
|---|---|---|---|---|
| LFG Enterprise Help Desk | 14,000 LFG employees | 96k voice + 31k chat / month | Connect us-east-1 with ACGR replica us-west-2 | SOX, PCI DSS (corporate card resets), GLBA |
| LFG Federal Services Help Desk | 6,500 employees of a federal agency client (contract task order) | 9k voice / month | must be FedRAMP High equivalent | public trust positions (moderate risk); US persons only; data must stay in a FedRAMP High boundary; on-site supervisors in Woodlawn, MD |

## Agents and sites

| Site | Agents | Allowed work |
|---|---|---|
| Charlotte (US) | 70 | all LFG queues; 25 of them hold public trust and also work the federal desk |
| Woodlawn, MD (US, on-site) | 18 | federal desk only (public trust) |
| Monterrey (MX, nearshore) | 40 | LFG Tier 1 queues only (password, general); no VIP, no HR/payroll |
| Pune (IN, offshore) | 12 developers + 6 L2 support | no live contacts; L2 sees LFG ServiceNow tickets; never federal data or recordings |

Supervisors see only their own teams' real-time metrics, recordings and evaluations. HR/payroll
queue contacts are visible only to the HR-cleared group. VIP desk (executives) only to VIP agents.

## Identity today

Okta (workforce, MFA with Okta Verify) for LFG; the federal client uses its own PIV-backed IdP
(Entra ID in Azure Government) for its staff, but agents are LFG employees. Joiner/mover/leaver
from Workday -> Okta. Agents currently have 3 logins (Avaya, Genesys, ServiceNow).

## Caller identity verification

- Password and MFA resets are 31% of calls and the top social-engineering vector (two incidents
  in 2026 where an attacker reset an executive's MFA by phone).
- Voice biometrics vendor Voice ID was considered in 2025 (it reached end of support in 2026).
- The CISO wants a tiered model: low-risk requests (ticket status) with light checks; credential
  resets and VIP requests with strong proofing. CLEAR (already used by LFG HR for onboarding) is
  an option the CISO wants evaluated.
- Employee portal (Okta SSO) has chat; callers who start chat from the portal are already
  authenticated.

## Compliance and retention

- Call recordings and transcripts: LFG 7 years for SOX-relevant desks, 1 year otherwise;
  federal: per the contract's records schedule (3 years), then destroy with evidence.
- PCI: card numbers must never be stored in recordings, transcripts or ServiceNow.
- Audit: who listened to which recording, who changed which flow, who changed access.
