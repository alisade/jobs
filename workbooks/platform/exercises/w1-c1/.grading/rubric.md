# Rubric: platform/w1-c1 Foundation guardrails over a Terraform plan
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Plan semantics | 15 | Full: evaluates `change.after`, skips deletes and data sources, treats `after_unknown` as a warning everywhere (never a silent pass, never a crash), cross-resource rules (GR005, GR008) evaluated once over the whole plan. Partial: one of these missing or done ad hoc per rule. Zero: parses HCL or string-matches the raw JSON. |
| 3 | Rule correctness and readability | 15 | Full: GR004 handles all three pin forms and rejects `\|\|`; GR005 only counts org-level parents and checks each shape; messages tell an engineer what to change; no duplicated logic. Partial: correct but regex soup or copy-pasted blocks. Zero: rules hard-code addresses from the fixture. |
| 4 | ANSWER.md: AWS mapping and production judgement | 20 | Full: maps each rule to the AWS control (SCP deny on CreateAccessKey vs `iam.disableServiceAccountKeyCreation`; IAM OIDC provider trust policy `sub`/`aud` conditions vs WIF `attribute_condition`; S3 Block Public Access vs public access prevention; OUs vs folders), says where it runs (after plan, before apply, required check), why plan not HCL, what `gcloud beta terraform vet` or OPA/conftest would add, and one limitation (for example, IAM granted outside Terraform or inherited from above the org root). Partial: generic. Zero: empty. |
Total: 100
