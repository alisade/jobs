# Rubric: ms/w5-t1 FieldOps 1.4 release to UAT fails at import
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause | 30 | Full: FieldOps 1.4 form and view require the contoso_regioncode column from ContosoCore 2.1.0.0; UAT has 2.0.3.0 and the manifest never imports Core 2.1 first. Partial (10-15): "missing dependency" without naming the component, solution and version gap. Zero: Account form layer, solution checker, or flags. |
| 3 | Evidence | 15 | Full: quotes the import error / MissingDependency, Solution.xml entries (types 2, 60, 26), UAT vs DEV solution lists, and artifacts showing Core 2.1 was built. Partial: one source. |
| 4 | Layering explanation | 10 | Full: Active (unmanaged) layer on Account form explained, does not block this import, hides future managed updates, remediation (move to source, remove active customizations, prevent edits in UAT). Partial: mentions layers vaguely. |
| 5 | Fix and preflight quality | 10 | Full: Core 2.1 managed before FieldOps, no hand-edited Solution.xml, no skip-dependency-check; preflight readable and wired before import. Partial: manifest fixed but preflight weak. |
| 6 | Trade-offs / production | 5 | Dependency gates, pinning the Core version per FieldOps build, ownership of shared components, blocking unmanaged changes downstream. |
Total: 100
