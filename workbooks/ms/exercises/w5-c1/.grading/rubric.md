# Rubric: ms/w5-c1 Dataverse access explainer
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Correctness of the security model reasoning | 15 | Full: depth evaluated against the assignment BU and the record's owning BU, team inheritance and the share-needs-Basic rule implemented deliberately (not by accident of test fitting). Partial: correct results but special cases bolted on per test. Zero: hard-coded ids or test-specific branches. |
| 3 | explain() quality | 10 | Full: one Grant per path, every field meaningful, detail readable by a support engineer. Partial: grants present but vague or duplicated. Zero: explain() is a thin wrapper around can(). |
| 4 | Ticket answers in ANSWER.md | 10 | Full: WO-1005 explained as a deliberate record share (by design, not a leak) and WO-1003 explained via team role Dispatch Pool with the CLI output pasted. Partial: one ticket answered. Zero: none. |
| 5 | Code quality | 5 | Typed, small functions, no duplication between can/explain, clear errors. |
| 6 | Trade-offs / production | 10 | Names real gaps (hierarchy security, column security, access team templates, cascade on reparent, RetrievePrincipalAccess / Check Access as ground truth, caching for scale). Partial: generic. Zero: missing. |
Total: 100
