# Rubric: connect/w8-c1 Flow promotion tool
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Mapping model | 15 | Full: resolves dev reference -> logical name -> target resource for every kind, Lambda qualifier handled by parsing the ARN, bare ids handled without corrupting ARNs, no global account-id search/replace shortcuts. Partial: works on the fixtures but relies on string replace of account/instance ids (breaks for DR where ids differ). Zero: hard-coded ARNs. |
| 3 | Fail-closed behavior | 15 | Full: unknown dev ARNs, unmapped resources and leftover dev references each reported with artifact + path + value; nothing emitted on any problem; foreign-account ARNs allowed deliberately. Partial: reports but still emits artifacts, or flags shared-services ARNs. |
| 4 | Code quality | 5 | Small pure functions, typed, no mutation of input, deterministic ordering, readable report. |
| 5 | ANSWER.md pipeline thinking | 15 | Full: places the tool in a pipeline (export from dev, promote, validate, deploy modules then flows via UpdateContactFlowModuleContent/UpdateContactFlowContent, run native flow test cases (StartTestCaseExecution) and a synthetic call), explains that regular flows have no alias API so rollback = redeploy previous artifact (keep artifacts versioned), manifests generated from IaC outputs or List* APIs, approvals for prod, and limits (semantic changes, prompts audio, Lex bot versions must be built/aliased in the target first). Partial: generic CI/CD text. |
Total: 100
