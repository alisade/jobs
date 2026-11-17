# ANSWER: audit/w1-t1 Every change passes after the prompt v2 rollout

## Approach

Reproduced with `make run` (pass=25). Compared one reviewer exception (S07) end to end: the recorded
freeform response, the parsed object, the report line. Then read the 2026.9.4 to 2026.10.2 diff.

## Root cause

Prompt v2 renamed the attribute keys (`approval_precedes_deploy`, `approver_independent`, `ci_green`)
and the release removed `response_schema` from the request, so the model returned the prompt's key
names. `ChangeAssessment` has `extra="ignore"` and defaults `approved_before_deploy`,
`independent_approver` and `tests_passed` to True. Evidence: freeform.json for CHG-104907 has
`"approval_precedes_deploy": false`; `ChangeAssessment.model_validate_json(...)` gives
`approved_before_deploy=True`; the run log shows `validation_errors=0`. Temperature and the model bump
are ruled out: the constrained recordings from the same model at the same settings have the right keys.

## Fix

Facts-only `ChangeFacts` (no defaults, extra forbid, aware timestamps, citations), schema on the
request, temperature 0, attributes computed in code from the deploy log and directory. `make run`
now gives pass=21 exception=4: S07 and S21 approval after deploy (S21 across time zones), S12
self-approval through an e-mail alias, S18 no approval.

## Trade-offs / what I would do in production

All CM-03 conclusions since 2026-10-06 need re-performance and the workpaper must say so. Prompt,
schema and contract changes to ControlPilot go through change control with a contract test and a
labeled eval set that includes known exceptions; a run with zero exceptions on a historically
non-zero control raises a review flag.
