# Rubric: ms/w6-c1 Tailspin work-order plug-ins
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 45 | points = 45 * passed / total from grade.sh |
| 2 | Pipeline correctness | 15 | Full: PreOperation sync, values set on Target, no Retrieve/Update, pre-image used, stage guard throws, no Depth-based skip, explains why. Partial: works but reads the row with Retrieve or relies on Depth. Zero: extra Update call or PostOperation. |
| 3 | Registration and custom API design | 15 | Full: one filtering attribute (not the primary key), pre-image with exactly the columns read, Action (not Function) justified by the Dataverse connector only performing actions, Global binding, None step type justified. Partial: correct values but no reasoning. Zero: Function, or all-columns image. |
| 4 | Error handling and messages | 10 | Full: InvalidPluginExecutionException with dispatcher-readable messages, registration errors distinguishable from business errors, input validation in the custom API. Partial: generic messages. Zero: raw exceptions leak. |
| 5 | Code quality and portability | 5 | C# 7.3-compatible, stateless (no instance fields holding request data), readable, tracing useful in a trace log. |
| 6 | ANSWER.md trade-offs | 10 | Full: concrete production points (e.g. PreValidation vs PreOperation cost of cancel, IsPrivate and Is Customizable=false before shipping, solution versioning of the assembly, trace log setting, App Insights). Partial: generic. Zero: missing. |
Total: 100
