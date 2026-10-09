# Rubric: ms/w3-t1 PROD gold table stale, pipeline green
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause | 30 | Full: the renamed notebook no longer matches the case-sensitive `item_name` filters in parameter.yml, fabric-cicd silently skips the replacement, PROD notebook keeps the DEV workspace + lakehouse binding and the scheduler identity can write to DEV. Partial (10-15): "parameter.yml did not replace the GUIDs" without why. Zero: throttling, executor loss, or "notebook bug". |
| 3 | Evidence | 15 | Full: cites the driver log abfss path with the DEV workspace id, the PROD vs DEV Delta history, the release log showing replacements only for silver, and a local render before/after. Partial: one or two sources. Zero: assertions only. |
| 4 | Fix quality and verification | 10 | Full: filter that survives renames, no hand-edited PROD GUIDs in source, guard wired into the release path, verified with render + guard output. Partial: item_name updated to the new name only. |
| 5 | Data remediation | 5 | Re-run PROD for the missing dates (idempotent replaceWhere) and clean the PROD rows out of DEV / flag the data handling issue. |
| 6 | Trade-offs / production | 10 | Separate identities per environment, freshness alerts, deployment rules or runtime binding as alternatives, one mechanism. Red herrings explicitly ruled out. |
Total: 100
