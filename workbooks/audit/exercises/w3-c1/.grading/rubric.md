# Rubric: audit/w3-c1 ADK CM-03 tester with scoped tools, guardrail callbacks and an execution log
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Least privilege | 15 | Full: only allowed tools are registered (defence in depth with the allow-list in the callback), scoping derives from the sample not from the model's arguments, blocked calls never run the tool body. Partial: callback only, write tool still offered. |
| 3 | Execution log | 15 | Full: one entry per call including blocked ones, digests of results, ordering; ANSWER.md explains what an auditor reconstructs and that the log must be append-only and stored outside the agent's reach. Partial: log present, reasoning thin. |
| 4 | Verification of the final answer | 10 | Full: strict summary model and cross-check against session state; mismatch, missing samples and free text all go to needs_review. |
| 5 | Design reasoning | 10 | Full: explains why guardrails are callbacks (deterministic, testable, independent of model behaviour) and how this maps onto ADK deployment, sessions and the posting's "scoped permissions, auditable agent activity". |
Total: 100
