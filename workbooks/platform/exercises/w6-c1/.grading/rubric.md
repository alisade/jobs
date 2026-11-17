# Rubric: platform/w6-c1 plan-gate: a Terraform plan JSON gate for CI
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Fail-closed behavior | 15 | Full: unknown actions and unknown format versions are errors (exit 2), a missing policy file is an error not "no policy", nothing prints PASS after an error, sensitive markers at any depth mask the whole attribute. Partial: one gap. Zero: unknown input silently passes. |
| 3 | Idiomatic Go | 10 | Full: small functions, errors returned and wrapped, no panics on odd JSON (type assertions with ok), deterministic ordering, Run testable through io.Writer. Partial: works but one large function or fmt.Println to os.Stdout. Zero: panics on fixtures. |
| 4 | ANSWER.md judgement | 15 | Full: plan JSON is what gets applied (modules, variables, provider defaults resolved; HCL review misses ForceNew defaults like the VPC case); gate the saved plan file that apply uses; limits (unknown after values, provider bugs, drift outside state, IAM side effects); relation to terraform vet / OPA (complement, not replacement). Partial: generic. Zero: empty. |
| 5 | Production rollout | 10 | Concrete: binary versioned and pinned in a shared CI template, policy files per repo class (migration vs normal), break-glass with an audited label, JSON report posted to the PR, metrics on violations. |
Total: 100
