# PagerDuty: keystone-workflows / LeadAssignment

**Incident KS-2291** - triggered Tue 2026-11-10 14:22 UTC - assigned: Marcus Oyelaran (SRE on call)

> [P2] keystone-workflows: workflow task failure rate > 5% for 15 min (task queue keystone-lead-assignment)

## Timeline (from #keystone-incidents)

- 14:05 release 2026.45 of keystone-workflows rolled out (2/2 worker pods replaced, PR #812).
- 14:22 alert above. Dashboard: `workflow_task_execution_failed` climbing on LeadAssignment only.
- 14:31 Dana Whitfield (sales ops): "managers approved four EMEA/AMER leads after lunch; the inbox still
  shows them as waiting and nobody got assigned. Also the 'approve by' time on the new inbox column keeps
  changing every time I refresh."
- 14:40 Priya Natarajan: "new leads created since 14:05 look fine end to end."
- 14:44 Marcus: "worker logs are full of activity timeout warnings from the enrichment vendor too, maybe
  the vendor is slow? Raising start_to_close on enrich_lead to 2 min in a hotfix branch."
- 14:52 Rollback is possible but would break the leads that started on 2026.45. Holding.

## What we exported

- `worker-2026-11-10.log` - excerpt from keystone-workflows pod `kw-worker-6c9f7-2xq4p`
- `../histories/*.json` - `temporal workflow show --output json` for four executions that started before
  14:05 (two awaiting approval, one escalated, one already completed)
- `pr-812.diff` - the change that shipped
