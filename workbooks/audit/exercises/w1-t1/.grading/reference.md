# Reference: audit/w1-t1

Root cause: three changes in 2026.10.2 combined into a silent failure.

1. Prompt v2 renamed the attribute keys to `approval_precedes_deploy`, `approver_independent`, `ci_green`.
2. The diff removed `response_schema=ChangeAssessment` from the request, so the model followed the
   prompt text rather than the contract's field names.
3. The contract was made "forward compatible" with `extra="ignore"`, and its attribute flags default
   to `True`. The renamed keys were dropped, the defaults filled in, and every sample passed with zero
   validation errors.

Evidence: `fixtures/recorded/freeform.json` for CHG-104907 says `"approval_precedes_deploy": false`;
`ChangeAssessment.model_validate_json` returns `approved_before_deploy=True`. `make run` prints
pass=25. With the fix: pass=21, exception=4 (S07, S12, S18, S21).

S21 shows why the model must not decide: even the freeform model said the approval preceded the
deploy, but 09:10+02:00 is 07:10Z, after the 06:30Z deploy.

Red herrings: temperature 0.4 changes wording, not key names; the constrained recordings come from
the same new model and are correct, so the model bump is not the cause.

Fix (in `.grading/solution/controlpilot/`): facts-only `ChangeFacts` contract with no defaults and
`extra="forbid"`; `response_schema=ChangeFacts`; attributes computed from the deploy log and the
directory. Impact: every CM-03 conclusion since 2026-10-06 must be re-performed; prompts and
contracts are program changes for ControlPilot itself and need review plus an eval gate.
