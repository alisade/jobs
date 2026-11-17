# Rubric: platform/w6-t1 The import agent ran terraform apply in staging
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: the guard is a deny list of regexes anchored at `^terraform apply`; `terraform -chdir=envs/stg apply -auto-approve` starts with `terraform -chdir`, so no pattern matches and the default is allow. The model retried after the first denial precisely by moving the subcommand. The injection in the label is the trigger; a deny-list over raw strings is the root cause. Partial (10-15): "regex was weak" without the -chdir mechanism or the allow-by-default. Zero: blames the model or the prompt. |
| 3 | Evidence | 20 | Full: quotes the label text, the 02:12:41 denial, the 02:12:55 allow with the command, the apply output (tier change), the approval log line (timeout, "continuing", result approved), the audit entry showing tf-apply-stg impersonated by import-agent, the replay output. Partial: one or two. |
| 4 | Second control and credentials | 10 | Full: approval.is_approved returned True on a timeout (fails open); the agent SA holds roles/iam.serviceAccountTokenCreator on tf-apply-stg ("temporary" since 2026-10-02) and the stg provider impersonates tf-apply-stg, so any terraform apply the agent runs has write credentials. Remove the binding; plan with a read-only identity. |
| 5 | Fix quality | 10 | Parsed commands, wrappers unwrapped, compound commands split, deny by default with an allow list, substitution denied; approval fails closed and checks the change id. Not a longer regex list. |
| 6 | Prevention | 5 | Read-only credentials as the real control (the guard is defense in depth), applies only via the reviewed pipeline, alerts on agent impersonation of apply SAs, injection cases in the agent's eval suite, the agent disabled until fixed. |
Total: 100
