# Rubric: platform/w5-c1 Admission gate for Helm-rendered manifests
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Supply-chain correctness | 15 | Full: registry check compares the host as a whole (no glob over the full reference), path prefix enforced, digest validated as sha256 + 64 hex, attestation matched on attestor AND digest AND repository, break-glass read from the pod template only and waives IMG003 only, every waiver recorded in `exceptions`. Partial: one gap. Zero: string `in` checks or break-glass waiving everything. |
| 3 | Code quality | 10 | Full: one place that finds pod templates and containers, rules data-driven or clearly separated, no duplicated traversal per rule, fails closed on unknown shapes (GateError, exit 2). Partial: works but repetitive or silently skips malformed docs. |
| 4 | ANSWER.md: findings and owner guidance | 10 | Full: names the five findings with the concrete fix per chart (pin riq-reindex to an Artifact Registry image by digest or remove the busybox wget pattern, rebuild rdm-worker through the prod pipeline so the prod-build-verified attestor signs it instead of qa-signoff, add a PDB, set automountServiceAccountToken false). Partial: lists findings only. |
| 5 | Production judgement | 15 | Full: CI gate as early feedback, Binary Authorization (dry-run then enforce, per-cluster policy, system images exempt) as the enforcement point because CI can be bypassed; break-glass approval and audit (Cloud Audit Logs entry, alert to security); attestation created by the build pipeline after the Artifact Analysis vulnerability gate (SLSA provenance); limits (Helm hooks, operator-created pods, runtime drift). Partial: generic. Zero: empty. |
Total: 100
