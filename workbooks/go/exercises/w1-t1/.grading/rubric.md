# Rubric: go/w1-t1 flagd returns 500 on every flag update
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified precisely | 30 | Full: `validate` returns a nil `*ValidationError` through an `error` return, producing a non-nil interface value (dynamic type `*ValidationError`, value nil), so `err != nil` in `Service.Put` is always true; fmt prints `<nil>` for it; the handler's `errors.As` matches but `FieldErrors()` is empty, so it falls to 500. Partial (12-20): "typed nil" named but the chain to the 500 / log line is not explained. Zero: blames omitempty, the debug log, the store or the mux. |
| 3 | Evidence | 15 | Full: commands and output excerpts, e.g. a test or snippet printing `%T`/`%v` of the returned error, `make repro` before/after, log line correlation with the deploy marker and commit `a41c9e2`. Partial: assertions without output. Zero: none. |
| 4 | Fix quality | 15 | Full: minimal change (return literal `nil` when there are no field errors, or keep a concrete type until the boundary), keeps all-fields reporting and `omitempty`, adds or describes a regression test for the valid path. Partial: works but by patching symptoms (e.g. handler treats empty ValidationError as success, or reverting the refactor). Zero: no fix. |
| 5 | Trade-offs / prevention | 10 | Full: concrete prevention, e.g. "return concrete types only at package boundaries, never a typed nil as error", `nilness`/`staticcheck` (SA4023) or `nilerr` linters in CI, a happy-path PUT test, canary/rollback plan. Partial: generic "add tests". Zero: empty. |
Total: 100
