# Rubric: ms/w10-t1 HR agent starts a leave request when asked for a balance
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause | 30 | Full: identifies the copy-pasted name/description on the Submit tool (identical to the balance tool) plus the undescribed balance input and balance-flavoured Submit input descriptions, and explains that generative orchestration selects tools by description. Partial: "the agent picks the wrong tool" without why. Zero: blames knowledge indexing, model quality or Teams. |
| 3 | Evidence | 15 | Full: cites activity maps (chosen tool, generated questions), analytics (invocations/abandonment), the eval run and solution history with excerpts. Partial: one source. Zero: none. |
| 4 | Red herring handled | 5 | Explicitly rules out the Facilities indexing warning with a reason. |
| 5 | Fix quality | 10 | Distinct names and descriptions that say what, when and what not; input descriptions; no stuffing; no deleted components. |
| 6 | Prevention | 10 | Evaluation test set as a release gate before import, review of cloned components, confirmation before writes, monitoring of abandonment. |
Total: 100
