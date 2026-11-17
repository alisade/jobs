# connect/w9-c1 - Identity, access and compliance architecture (enterprise + federal desk)

**Type:** design | **Estimate:** 2-3 hours | **Study plan:** Week 9 (SAML/SSO, RBAC and tag-based access control, identity verification incl. CLEAR, GovCloud/FedRAMP, retention and audit); Week 1 (ACGR)

## Scenario

LFG's help desk serves its own 14,000 employees and, under a federal task order, 6,500
employees of a federal agency (on-site supervisors in Woodlawn, MD; public trust positions).
Agents sit in Charlotte, Woodlawn and Monterrey; developers and L2 support in Pune. Two MFA
resets by phone were social-engineered this year. The CISO and the client's ISSO want one
architecture that covers agent identity, who can see what, caller verification, the federal
boundary and retention.

## What you have

| Path | What it is |
|---|---|
| `inputs/requirements.md` | desks, sites and allowed work, identity today, verification needs, compliance and retention |
| `DESIGN.md` | the template you fill in (the deliverable) |

## Your task

1. Fill in every section of `DESIGN.md`. Name the Connect and AWS features you rely on and
   their limits (verify them in the study guide's Week 9 links).
2. Map every access rule in `inputs/` (Monterrey, Pune, HR, VIP, supervisors, federal) to a
   concrete mechanism.
3. Fill in `ANSWER.md` (Approach, Fix = summary of key decisions, Trade-offs).

## Acceptance criteria (what the grader checks)

No automated tests (grade.sh reports 0/0). The rubric scores the federal boundary (GovCloud,
FedRAMP, personnel), agent identity and lifecycle, the authorization model with real
tag-based access control limits, tiered caller verification (including CLEAR and portal chat),
and data protection, retention and audit.

## How to run

```bash
make setup
make test      # completeness report
# from workbooks/ in Claude Code: /grade connect/w9-c1
make clean
```
