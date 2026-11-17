# Reference: connect/w1-c3

Model answer: `.grading/solution/DESIGN.md`.

What great looks like:
- Uses Amazon Connect Global Resiliency (ACGR) as the only AWS-supported multi-region pattern:
  ReplicateInstance to the paired region (us-east-1 <-> us-west-2), numbers claimed to a traffic
  distribution group, telephony and agent distribution moved in 10 percent increments, SAML 2.0 with
  the global sign-in endpoint, Enterprise Support as a prerequisite.
- Knows what does not move by itself: chat widget/API endpoints are per region, numbers on the instance
  (not the TDG) stay put, Lambdas/Lex/data/secrets/KMS/allow lists need their own plan.
- Writes a runbook someone else can execute at 3 AM: triggers, owner, timed steps, verification,
  communications, failback and rollback.
- Mentions global routing (active-active cross-region agent routing, default for ACGR instances created
  on/after 2026-09-01) and makes a reasoned choice.
Common misses: Route 53 or DNS "for calls", forgetting the replica's quotas, forgetting the ServiceNow
allow list or the KMS key for recordings, no drill plan.
