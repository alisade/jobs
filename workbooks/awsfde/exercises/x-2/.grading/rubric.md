# Rubric: awsfde/x-2 From three one-off fixes to a reusable tenant-isolation kit
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 0 | Does not apply: review-only design exercise (grade.sh reports 0/0). |
| 2 | Pattern diagnosis | 15 | Full: the common pattern is that tenant scope was an optional, per-call decision made in application code (a fallback, an argument, a header that was not set), with no second layer below it; the fix in each case was local, so the same class recurs elsewhere. Partial: lists the incidents without the shared cause. |
| 3 | Kit design | 25 | Full: concrete components with clear guarantees: a tenant-context library in TS and Python as the only source of tenant (from verified claims), a Retrieve wrapper that always injects the filter and rejects tenant keys in user filters, a CDK construct (TenantScopedTool) that creates the Lambda, the session-tag role with ForAllValues:StringLike LeadingKeys and no Scan, the Gateway target, and no-store defaults; a CDN behavior helper (CachingDisabled for authenticated paths); a cross-tenant attack test kit. Uses the stable aws-cdk-lib/aws-bedrockagentcore constructs (Policy included as of 2.277). Partial: components named without guarantees. |
| 4 | API sketch | 10 | Full: realistic signatures for both languages and a CDK example short enough that a team sees the adoption cost. Partial: one language or pseudo-code only. |
| 5 | Defense in depth table | 10 | Full: every incident mapped to at least two layers that would stop it, including one beyond app code (IAM, data filter, edge, tests). Partial: one layer each. |
| 6 | Adoption, evidence and AppSec | 20 | Full: phased rollout ordered by risk (tenant-data writes and retrieval first), a day-or-less adoption per service, the AppSec checklist replaced by kit usage plus the attack tests in CI (review time measured), static checks (lint or synth-time rules) that flag direct Retrieve or raw tenant reads, runtime alarms, a vendor-review evidence pack, owners and versioning. Partial: "teams should adopt it". |
| 7 | Judgement | 10 | Full: what not to generalize (tenant-specific business rules, admin tools as separate targets rather than a flag, one cache policy for everything), risks of a shared library (blast radius, versioning, ownership by three engineers) and mitigations. Partial: none. |
| 8 | Communication and FDE story | 10 | A reviewer could approve or challenge each decision; the two-minute story has a situation, ambiguity, narrowing, fix, reusable pattern and a measured result. |
Total: 100
