# Rubric: javaai/w1-c1 Catalog API: validation, problem details and a schema that enforces its own rules
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Validation design | 15 | Full: constraints on the request records, a class-level (cross-field) constraint for answerIndex and distinct options that reports the right property path, `@Valid` at the controller boundary, no hand-rolled if-chains duplicating annotations. Partial (5-10): rules in the controller with manual checks, or correct but field names wrong. |
| 3 | Error handling | 10 | One `@RestControllerAdvice` (ideally extending ResponseEntityExceptionHandler) producing RFC 9457 problem details; 404/409 via typed exceptions; DataIntegrityViolationException mapped to 409 as the race backstop; no stack traces or SQL in bodies. |
| 4 | Schema migration | 15 | New V2+ migration, V1 untouched; unique, FK and CHECK constraints named; index leading with learner_id justified by the query it serves. ANSWER.md explains why the database is the last line of defence (other writers, races) and how to roll out against dirty data (find duplicates, clean, then add the constraint; CONCURRENTLY / NOT VALID then VALIDATE on PostgreSQL). |
| 5 | Learner-safety thinking | 5 | Learner view is a separate record without key or explanation; ANSWER.md notes the explanation is revealed only after an attempt and that the same rule must hold in the AI tutor. |
| 6 | Code quality and trade-offs | 5 | Small focused changes, records stay immutable, sensible names; trade-offs section mentions keyset pagination or API versioning. |
Total: 100
