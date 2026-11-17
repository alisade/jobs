# Rubric: backend/w6-t1 Lead workflows stuck after Tuesday's deploy
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause | 25 | Full: nondeterminism on replay: in-flight 2026.44 histories record score_lead then propose_owner, the new code issues enrich_lead in between, the command does not match the recorded event (TMPRL1100), the workflow task fails and retries forever; only pre-deploy executions are affected. Plus the second defect: datetime.now() in workflow code makes sla_deadline differ per replay, and the sandbox that would have flagged it was disabled. Partial: names nondeterminism without the mechanism, or misses the datetime.now defect. Zero: blames the vendor timeouts. |
| 3 | Evidence | 20 | Full: quotes the TMPRL1100 log line, make replay output before and after, the diff lines, the changing sla_deadline log lines, and ties "new leads fine" to replay. Partial: one or two of these. |
| 4 | Red herring | 5 | Explains why activity timeouts are retried and cannot fail workflow tasks; the hotfix would not help. |
| 5 | Fix quality | 10 | workflow.patched around the new activity (or worker versioning with a reason), workflow.now(), sandbox re-enabled; histories untouched. Deduct for deleting histories, renaming activities, or terminating executions. |
| 6 | Rollout and prevention | 10 | Patch lifecycle (patched, deprecate_patch, remove after old executions close), CI replay of production histories, keep the sandbox on. |
Total: 100
